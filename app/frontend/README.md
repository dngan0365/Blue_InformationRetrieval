# Document Search System

Hệ thống tìm kiếm tài liệu mạnh mẽ sử dụng thuật toán BM25 với giao diện web đẹp mắt.

## 🚀 Tính năng

### Backend (FastAPI)
- ✅ Thuật toán BM25F cho tìm kiếm chính xác
- ✅ Tích hợp PageRank scores
- ✅ Tùy chỉnh tham số BM25 (B, K1)
- ✅ Điều chỉnh trọng số cho title và content
- ✅ Trích xuất snippet thông minh dựa trên query
- ✅ Chuẩn hóa điểm số thành phần trăm
- ✅ API endpoints RESTful

### Frontend (Next.js + React)
- ✅ Giao diện hiện đại với gradient animations
- ✅ Highlight từ khóa trong kết quả
- ✅ Sắp xếp theo relevance, pagerank, hoặc title
- ✅ Advanced parameters panel
- ✅ Hiển thị thời gian tìm kiếm
- ✅ Loading states và error handling
- ✅ Responsive design

## 📦 Cài đặt

### Backend

1. **Cài đặt dependencies:**
```bash
pip install -r requirements.txt
```

2. **Cấu hình paths trong main.py:**
```python
INDEX_DIR = "ind"  # Đường dẫn tới Whoosh index
META_CSV = "../../3.AnalysisData/output/final_document_tfidf_pagerank.csv"
JSON_DIR = "../../3.AnalysisData/output/docs_no_stop.json"
```

3. **Chạy server:**
```bash
python main.py
# hoặc
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Server sẽ chạy tại: http://localhost:8000

### Frontend

1. **Cài đặt dependencies (nếu chưa có):**
```bash
npm install
# hoặc
yarn install
```

2. **Thay thế file page.tsx trong app directory**

3. **Chạy development server:**
```bash
npm run dev
# hoặc
yarn dev
```

App sẽ chạy tại: http://localhost:3000

## 🎯 Sử dụng

### API Endpoints

#### 1. Health Check
```bash
GET http://localhost:8000/
```

#### 2. Search Documents
```bash
POST http://localhost:8000/search
Content-Type: application/json

{
  "query": "machine learning",
  "model": "bm25",
  "limit": 100,
  "B": 0.75,
  "K1": 1.2,
  "title_boost": 1.5,
  "content_boost": 1.0
}
```

**Response:**
```json
[
  {
    "doc_id": "123",
    "title": "Introduction to Machine Learning",
    "url": "https://example.com/ml-intro",
    "snippet": "...machine learning is a subset of artificial intelligence...",
    "score": 15.4321,
    "relevance_percentage": 98.5,
    "pagerank_score": 0.002345
  }
]
```

#### 3. Get Statistics
```bash
GET http://localhost:8000/stats
```

### Web Interface

1. Nhập query vào ô search
2. (Tùy chọn) Click "Advanced Parameters" để tinh chỉnh
3. Click "Search" hoặc nhấn Enter
4. Sắp xếp kết quả theo Relevance, PageRank, hoặc Title
5. Click vào title để mở document

## ⚙️ Tham số BM25

### B Parameter (0.0 - 1.0)
- **Mặc định: 0.75**
- Điều chỉnh ảnh hưởng của document length
- B=0: Không quan tâm đến độ dài
- B=1: Normalize hoàn toàn theo độ dài

### K1 Parameter (1.0 - 3.0)
- **Mặc định: 1.2**
- Điều chỉnh term frequency saturation
- K1 thấp: Saturation nhanh hơn
- K1 cao: Term frequency quan trọng hơn

### Field Boosts
- **Title Boost (mặc định: 1.5)**: Trọng số cho title field
- **Content Boost (mặc định: 1.0)**: Trọng số cho content field

## 📊 Cấu trúc dữ liệu

### Meta CSV (final_document_tfidf_pagerank.csv)
```csv
doc_id,title,url,pagerank
1,Document Title,https://example.com,0.002345
```

### Documents JSON (docs_no_stop.json)
```json
{
  "1": {
    "title": "Document Title",
    "content": "Document content here..."
  }
}
```

### Whoosh Index Directory (ind/)
- Chứa Whoosh index files
- Được tạo từ quá trình indexing

## 🎨 Tùy chỉnh giao diện

File `page.tsx` sử dụng Tailwind CSS với:
- Gradient animations
- Glassmorphism effects
- Custom color schemes
- Responsive breakpoints

Để thay đổi theme, chỉnh sửa các class trong component:
- Background: `from-slate-900 via-purple-900 to-slate-900`
- Primary color: `purple-600`, `pink-600`
- Accent color: `yellow-400`

## 🔧 Troubleshooting

### Backend không khởi động
- Kiểm tra đường dẫn INDEX_DIR, META_CSV, JSON_DIR
- Đảm bảo Whoosh index đã được build
- Kiểm tra logs khi startup

### Không có kết quả
- Kiểm tra query format
- Thử tăng limit
- Điều chỉnh B và K1 parameters
- Kiểm tra index có documents không

### CORS errors
- Đảm bảo backend đang chạy
- Kiểm tra allow_origins trong main.py
- Kiểm tra URL trong frontend (http://localhost:8000)

## 📝 License

MIT License