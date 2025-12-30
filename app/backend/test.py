import requests
import json

# API endpoint
BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test health check endpoint"""
    print("=" * 60)
    print("Testing Health Check...")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_search(query, limit=10, **kwargs):
    """Test search endpoint"""
    print("=" * 60)
    print(f"Searching for: '{query}'")
    print("=" * 60)
    
    payload = {
        "query": query,
        "model": "bm25",
        "limit": limit,
        **kwargs
    }
    
    print(f"Request payload: {json.dumps(payload, indent=2)}")
    print()
    
    response = requests.post(
        f"{BASE_URL}/search",
        json=payload
    )
    
    if response.status_code == 200:
        results = response.json()
        print(f"Found {len(results)} results")
        print()
        
        for i, result in enumerate(results[:5], 1):  # Show top 5
            print(f"Result #{i}")
            print(f"  Doc ID: {result['doc_id']}")
            print(f"  Title: {result['title']}")
            print(f"  URL: {result['url']}")
            print(f"  Score: {result['score']:.4f}")
            print(f"  Relevance: {result['relevance_percentage']:.2f}%")
            if result.get('pagerank_score'):
                print(f"  PageRank: {result['pagerank_score']:.6f}")
            print(f"  Snippet: {result['snippet'][:100]}...")
            print()
    else:
        print(f"Error {response.status_code}: {response.text}")
    print()

def test_stats():
    """Test statistics endpoint"""
    print("=" * 60)
    print("Getting Statistics...")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/stats")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_advanced_search():
    """Test search with custom parameters"""
    print("=" * 60)
    print("Testing Advanced Search with Custom Parameters")
    print("=" * 60)
    
    test_search(
        query="machine learning",
        limit=5,
        B=0.85,
        K1=1.5,
        title_boost=2.0,
        content_boost=1.0
    )

if __name__ == "__main__":
    print("\n🚀 Starting API Tests\n")
    
    try:
        # Test 1: Health check
        test_health_check()
        
        # Test 2: Statistics
        test_stats()
        
        # Test 3: Basic search
        test_search("machine learning", limit=10)
        
        # Test 4: Advanced search with custom parameters
        test_advanced_search()
        
        # Test 5: Another query
        test_search("artificial intelligence", limit=5)
        
        print("✅ All tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the API server.")
        print("Make sure the FastAPI server is running at http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")