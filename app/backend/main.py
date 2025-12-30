from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import pandas as pd
from whoosh import index, qparser
from whoosh.qparser import MultifieldParser
from whoosh.scoring import BM25F
from whoosh.index import open_dir
import os
import nltk
from nltk import sent_tokenize
import re
import unicodedata
from pyvi import ViTokenizer

nltk.download('punkt_tab')
nltk.download('stopwords')

app = FastAPI(title="Document Search API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js development
        "http://localhost:3001",  # Alternative port
        "https://blue-information-retrieval.vercel.app", # Production frontend URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
INDEX_DIR = "./retrieval/ind"
META_CSV = "./retrieval/final_document_tfidf_pagerank.csv"
DATA_CLEAN_DIR = "./retrieval/data_clean"
IMAGE_CSV = "./retrieval/docs_with_images.csv"  # File CSV chứa URL ảnh
STOPWORDS_PATH = "./retrieval/vietnamese-stopwords-dash.txt"

# Global variables
ix = None
meta_df = None
image_df = None  # DataFrame chứa mapping doc_id -> image_url
docs_cache = {}
pagerank_dict = {}
vi_stopwords = None


class SearchRequest(BaseModel):
    query: str
    model: str = "bm25"
    limit: int = 100
    B: float = 0.75
    K1: float = 1.2
    title_boost: float = 1.5
    content_boost: float = 1.0


class SearchResult(BaseModel):
    doc_id: str
    title: str
    url: str
    snippet: str
    score: float
    relevance_percentage: float
    image_url: Optional[str] = None
    pagerank_score: Optional[float] = None
    total_words: Optional[int] = None
    unique_words: Optional[int] = None
    top_words: Optional[str] = None
    top_tfidf: Optional[str] = None
    avg_tfidf: Optional[float] = None
    final_score: Optional[float] = None


def split_sentences(text):
    return sent_tokenize(text)


def tokenize_vi_sentence_level(text: str) -> list[str]:
    sentences = sent_tokenize(text)
    tokens = []
    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue
        sent_tokens = ViTokenizer.tokenize(sent)
        tokens.extend(sent_tokens.split())
    return tokens


VI_TOKEN_REGEX = re.compile(
    r"[a-zàáạảãâầấậẩẫăằắặẳẵ"
    r"èéẹẻẽêềếệểễ"
    r"ìíịỉĩ"
    r"òóọỏõôồốộổỗơờớợởỡ"
    r"ùúụủũưừứựửữ"
    r"ỳýỵỷỹđ0-9_]+$"
)


def is_valid_vi_token(token: str) -> bool:
    return bool(VI_TOKEN_REGEX.fullmatch(token))


def load_stopwords(path):
    with open(path, "r", encoding="utf-8") as f:
        stopwords = set(line.strip().lower() for line in f if line.strip())
    return stopwords


def clean_text(text):
    if text is None:
        return ""
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"http\S+|www\S+", "", text)
    text = re.sub(r"[.,!?]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def preprocess_query(query: str, stopwords: set[str] | None = None) -> str:
    query = clean_text(query)
    tokens = tokenize_vi_sentence_level(query)
    processed_tokens = []
    for tok in tokens:
        tok = tok.lower()
        if not is_valid_vi_token(tok):
            continue
        if tok.isnumeric():
            continue
        if stopwords and tok in stopwords:
            continue
        processed_tokens.append(tok)
    return " ".join(processed_tokens)


def load_pagerank(meta_csv: str) -> Dict[str, float]:
    """Load PageRank scores from CSV"""
    try:
        df = pd.read_csv(meta_csv)
        if 'pagerank' in df.columns and 'id' in df.columns:
            return dict(zip(df['id'].astype(str), df['pagerank']))
        return {}
    except Exception as e:
        print(f"Warning: Could not load PageRank scores: {e}")
        return {}


def load_images_csv(image_csv: str) -> pd.DataFrame:
    """Load image URLs from CSV file"""
    try:
        if not os.path.exists(image_csv):
            print(f"⚠️ Image CSV not found: {image_csv}")
            return pd.DataFrame(columns=['doc_id', 'image_url'])
        
        df = pd.read_csv(image_csv)
        
        # Đảm bảo có cả 2 cột cần thiết
        if 'doc_id' not in df.columns or 'image_url' not in df.columns:
            print("⚠️ Image CSV missing required columns: doc_id, image_url")
            return pd.DataFrame(columns=['doc_id', 'image_url'])
        
        # Convert doc_id to string để dễ mapping
        df['doc_id'] = df['doc_id'].astype(str)
        
        # Loại bỏ các dòng có image_url null/empty
        df = df[df['image_url'].notna() & (df['image_url'] != '')]
        
        print(f"✅ Loaded {len(df)} image URLs from CSV")
        return df
        
    except Exception as e:
        print(f"❌ Error loading image CSV: {e}")
        return pd.DataFrame(columns=['doc_id', 'image_url'])


def get_image_url(doc_id: str) -> Optional[str]:
    """Get image URL for a document from CSV"""
    global image_df
    
    if image_df is None or image_df.empty:
        return None
    
    try:
        # Tìm image_url theo doc_id
        result = image_df[image_df['doc_id'] == str(doc_id)]
        
        if not result.empty:
            image_url = result.iloc[0]['image_url']
            # Kiểm tra URL hợp lệ
            if pd.notna(image_url) and str(image_url).strip() != '':
                return str(image_url)
        
        return None
        
    except Exception as e:
        print(f"Error getting image URL for doc {doc_id}: {e}")
        return None


def load_document_content(doc_id: str) -> str:
    """Load document content from data_clean directory"""
    global docs_cache
    
    if doc_id in docs_cache:
        return docs_cache[doc_id]
    
    try:
        file_path = os.path.join(DATA_CLEAN_DIR, f"{doc_id}.txt")
        
        if not os.path.exists(file_path):
            print(f"Warning: File not found: {file_path}")
            return ""
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        docs_cache[doc_id] = content
        return content
        
    except Exception as e:
        print(f"Error loading document {doc_id}: {e}")
        return ""


def get_snippet(doc_id: str, query_terms: List[str], max_length: int = 200) -> str:
    """Extract relevant snippet from document based on query terms"""
    content = load_document_content(doc_id)
    
    if not content or content.strip() == "":
        return "Không có nội dung xem trước."
    
    try:
        content_lower = content.lower()
        query_lower = [term.lower() for term in query_terms if term.strip()]
        
        if not query_lower:
            words = content.split()
            snippet_words = words[:30]
            snippet = ' '.join(snippet_words)
            if len(snippet) > max_length:
                snippet = snippet[:max_length] + "..."
            return snippet
        
        best_pos = 0
        max_matches = 0
        
        words = content.split()
        window_size = min(30, len(words))
        
        for i in range(max(1, len(words) - window_size + 1)):
            window = ' '.join(words[i:i+window_size]).lower()
            matches = sum(1 for term in query_lower if term in window)
            if matches > max_matches:
                max_matches = matches
                best_pos = i
        
        snippet_words = words[best_pos:best_pos+window_size]
        snippet = ' '.join(snippet_words)
        
        if len(snippet) > max_length:
            snippet = snippet[:max_length] + "..."
        
        if best_pos > 0:
            snippet = "..." + snippet
        
        return snippet
        
    except Exception as e:
        print(f"Error generating snippet for doc {doc_id}: {e}")
        return "Lỗi khi tạo đoạn trích."


def bm25_search(ix, query_str: str, vi_stopwords: set[str] | None = None, top_k: int = 100, 
                B: float = 0.75, K1: float = 1.2,
                title_boost: float = 1.5, content_boost: float = 1.0) -> Dict[str, float]:
    """BM25 search with title and content fields"""
    query_str = preprocess_query(query_str, stopwords=vi_stopwords)
    results = {}
    weighting = BM25F(B=B, K1=K1)
    
    with ix.searcher(weighting=weighting) as searcher:
        field_boosts = {
            "title": title_boost,
            "content": content_boost
        }
        
        parser = MultifieldParser(
            ["title", "content"],
            schema=ix.schema,
            fieldboosts=field_boosts,
            group=qparser.OrGroup
        )
        
        q = parser.parse(query_str)
        hits = searcher.search(q, limit=top_k)
        
        for hit in hits:
            results[str(hit["docid"])] = float(hit.score)
    
    return results


def normalize_scores(scores: Dict[str, float]) -> Dict[str, float]:
    """Normalize scores to percentage (0-100)"""
    if not scores:
        return {}
    max_score = max(scores.values())
    if max_score == 0:
        return {k: 0.0 for k in scores}
    return {k: (v / max_score) * 100 for k, v in scores.items()}


@app.on_event("startup")
async def startup_event():
    """Initialize index and load data on startup"""
    global ix, meta_df, image_df, pagerank_dict, vi_stopwords
    
    try:
        # Load Whoosh index
        if os.path.exists(INDEX_DIR):
            ix = open_dir(INDEX_DIR)
            print("✅ Loaded Whoosh index")
        else:
            print("❌ Index directory not found:", INDEX_DIR)
        
        # Load metadata
        if os.path.exists(META_CSV):
            meta_df = pd.read_csv(META_CSV)
            print(f"✅ Loaded {len(meta_df)} documents metadata")
        else:
            print("❌ Metadata CSV not found:", META_CSV)
        
        # Load image CSV
        image_df = load_images_csv(IMAGE_CSV)
        
        # Check data_clean directory
        if os.path.exists(DATA_CLEAN_DIR):
            num_files = len([f for f in os.listdir(DATA_CLEAN_DIR) if f.endswith('.txt')])
            print(f"✅ Found {num_files} text files in {DATA_CLEAN_DIR}")
        else:
            print("❌ Data clean directory not found:", DATA_CLEAN_DIR)
        
        # Load PageRank scores
        pagerank_dict = load_pagerank(META_CSV)
        print(f"✅ Loaded PageRank scores for {len(pagerank_dict)} documents")
        
        # Load StopWords
        if os.path.exists(STOPWORDS_PATH):
            vi_stopwords = load_stopwords(STOPWORDS_PATH)
            print(f"✅ Loaded {len(vi_stopwords)} Vietnamese stopwords")
        else:
            print("⚠️ Stopwords file not found, continuing without stopwords")
            vi_stopwords = set()
        
    except Exception as e:
        print(f"❌ Error during startup: {e}")
        raise


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "Document Search API is running",
        "total_documents": len(meta_df) if meta_df is not None else 0,
        "total_images": len(image_df) if image_df is not None else 0,
        "data_clean_dir": DATA_CLEAN_DIR,
        "image_csv": IMAGE_CSV,
        "index_dir": INDEX_DIR
    }


@app.post("/search", response_model=List[SearchResult])
async def search(request: SearchRequest):
    """Search documents using BM25 algorithm"""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    if ix is None or meta_df is None:
        raise HTTPException(status_code=503, detail="Search index not initialized")
    
    try:
        raw_scores = bm25_search(
            ix, 
            request.query,
            vi_stopwords=vi_stopwords,
            top_k=request.limit,
            B=request.B,
            K1=request.K1,
            title_boost=request.title_boost,
            content_boost=request.content_boost
        )
        
        if not raw_scores:
            return []
        
        normalized_scores = normalize_scores(raw_scores)
        query_terms = request.query.split()
        
        results = []
        for doc_id, score in raw_scores.items():
            doc_row = meta_df[meta_df['id'].astype(str) == doc_id]
            
            if doc_row.empty:
                continue
            
            doc_info = doc_row.iloc[0]
            snippet = get_snippet(doc_id, query_terms, max_length=300)
            pr_score = pagerank_dict.get(doc_id)
            
            # Lấy image_url từ CSV
            image_url = get_image_url(doc_id)
            
            result = SearchResult(
                doc_id=doc_id,
                title=str(doc_info.get('title', 'Untitled')),
                url=str(doc_info.get('url', '')),
                snippet=snippet,
                score=round(score, 4),
                relevance_percentage=round(normalized_scores[doc_id], 2),
                image_url=image_url,
                pagerank_score=round(pr_score, 6) if pr_score else None,
                total_words=int(doc_info.get('total_words', 0)) if pd.notna(doc_info.get('total_words')) else None,
                unique_words=int(doc_info.get('unique_words', 0)) if pd.notna(doc_info.get('unique_words')) else None,
                top_words=str(doc_info.get('top_words', '')) if pd.notna(doc_info.get('top_words')) else None,
                top_tfidf=str(doc_info.get('top_tfidf', '')) if pd.notna(doc_info.get('top_tfidf')) else None,
                avg_tfidf=round(float(doc_info.get('avg_tfidf', 0)), 6) if pd.notna(doc_info.get('avg_tfidf')) else None,
                final_score=round(float(doc_info.get('final_score', 0)), 6) if pd.notna(doc_info.get('final_score')) else None
            )
            
            results.append(result)
        
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:request.limit]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@app.get("/stats")
async def get_stats():
    """Get statistics about the search index"""
    if meta_df is None:
        raise HTTPException(status_code=503, detail="Index not initialized")
    
    num_cached_docs = len(docs_cache)
    num_txt_files = 0
    
    if os.path.exists(DATA_CLEAN_DIR):
        num_txt_files = len([f for f in os.listdir(DATA_CLEAN_DIR) if f.endswith('.txt')])
    
    return {
        "total_documents": len(meta_df),
        "total_images": len(image_df) if image_df is not None else 0,
        "text_files_available": num_txt_files,
        "cached_documents": num_cached_docs,
        "pagerank_scores": len(pagerank_dict),
        "index_directory": INDEX_DIR,
        "data_clean_directory": DATA_CLEAN_DIR,
        "image_csv": IMAGE_CSV
    }


@app.get("/document/{doc_id}")
async def get_document(doc_id: str):
    """Get full document content and metadata"""
    if meta_df is None:
        raise HTTPException(status_code=503, detail="Index not initialized")
    
    doc_row = meta_df[meta_df['id'].astype(str) == doc_id]
    
    if doc_row.empty:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc_info = doc_row.iloc[0]
    content = load_document_content(doc_id)
    image_url = get_image_url(doc_id)
    
    return {
        "doc_id": doc_id,
        "title": str(doc_info.get('title', 'Untitled')),
        "url": str(doc_info.get('url', '')),
        "content": content,
        "image_url": image_url,
        "pagerank": float(doc_info.get('pagerank', 0)) if pd.notna(doc_info.get('pagerank')) else None,
        "total_words": int(doc_info.get('total_words', 0)) if pd.notna(doc_info.get('total_words')) else None,
        "unique_words": int(doc_info.get('unique_words', 0)) if pd.notna(doc_info.get('unique_words')) else None,
        "top_words": str(doc_info.get('top_words', '')) if pd.notna(doc_info.get('top_words')) else None,
        "top_tfidf": str(doc_info.get('top_tfidf', '')) if pd.notna(doc_info.get('top_tfidf')) else None,
        "avg_tfidf": float(doc_info.get('avg_tfidf', 0)) if pd.notna(doc_info.get('avg_tfidf')) else None,
        "final_score": float(doc_info.get('final_score', 0)) if pd.notna(doc_info.get('final_score')) else None
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)