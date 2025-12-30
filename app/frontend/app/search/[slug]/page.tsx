/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import { useState, useEffect, use } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import Link from "next/link";

type Result = {
  doc_id: string;
  title: string;
  url: string;
  snippet: string;
  score: number;
  relevance_percentage: number;
  image_url?: string;
  pagerank_score?: number;
  total_words?: number;
  unique_words?: number;
  top_words?: string;
  top_tfidf?: string;
  avg_tfidf?: number;
  final_score?: number;
};

type SortOption = "relevance" | "pagerank" | "title";

export default function SearchPage({ params }: { params: Promise<{ slug: string }> }) {
  const resolvedParams = use(params);
  const router = useRouter();
  const initialQuery = decodeURIComponent(resolvedParams.slug);
  
  const [query, setQuery] = useState(initialQuery);
  const [results, setResults] = useState<Result[]>([]);
  const [displayResults, setDisplayResults] = useState<Result[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searchTime, setSearchTime] = useState(0);
  const [sortBy, setSortBy] = useState<SortOption>("relevance");
  const [showAdvanced, setShowAdvanced] = useState(false);
  
  // Advanced parameters
  const [bParam, setBParam] = useState(0.75);
  const [k1Param, setK1Param] = useState(1.2);
  const [titleBoost, setTitleBoost] = useState(1.5);
  const [contentBoost, setContentBoost] = useState(1.0);
  const [resultLimit, setResultLimit] = useState(100);

  // Auto search on mount
  useEffect(() => {
    if (initialQuery) {
      performSearch(initialQuery);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Sort results when sort option changes
  useEffect(() => {
    if (results.length === 0) return;
    
    const sorted = [...results].sort((a, b) => {
      switch (sortBy) {
        case "pagerank":
          return (b.pagerank_score || 0) - (a.pagerank_score || 0);
        case "title":
          return a.title.localeCompare(b.title);
        case "relevance":
        default:
          return b.score - a.score;
      }
    });
    
    setDisplayResults(sorted);
  }, [sortBy, results]);

  const performSearch = async (searchQuery: string) => {
    setLoading(true);
    setError("");
    const startTime = performance.now();

    try {
      const res = await fetch("http://localhost:8000/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: searchQuery.trim(),
          model: "bm25",
          limit: resultLimit,
          B: bParam,
          K1: k1Param,
          title_boost: titleBoost,
          content_boost: contentBoost,
        }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Search failed");
      }

      const data = await res.json();
      const endTime = performance.now();
      
      setResults(data);
      setDisplayResults(data);
      setSearchTime((endTime - startTime) / 1000);
      
    } catch (err: any) {
      setError(err.message || "Failed to connect to search server");
      setResults([]);
      setDisplayResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    if (!query.trim()) {
      setError("Vui lòng nhập từ khóa tìm kiếm");
      return;
    }
    router.push(`/search/${encodeURIComponent(query.trim())}`);
    performSearch(query.trim());
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !loading) {
      handleSearch();
    }
  };

  const resetAdvanced = () => {
    setBParam(0.75);
    setK1Param(1.2);
    setTitleBoost(1.5);
    setContentBoost(1.0);
    setResultLimit(100);
  };

  const highlightText = (text: string, query: string) => {
    if (!query.trim()) return text;
    
    const terms = query.trim().toLowerCase().split(/\s+/);
    let highlighted = text;
    
    terms.forEach(term => {
      const regex = new RegExp(`(${term})`, 'gi');
      highlighted = highlighted.replace(regex, '<mark class="bg-amber-200 text-gray-900 px-0.5 rounded">$1</mark>');
    });
    
    return highlighted;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header with Search */}
      <header className="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center gap-6">
            {/* Logo */}
            <button
              onClick={() => router.push("/")}
              className="flex items-center gap-3 flex-shrink-0 group"
            >
              <div className="w-10 h-10 bg-gradient-to-r from-cyan-500 to-teal-500 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <span className="text-xl font-bold bg-gradient-to-r from-cyan-600 to-teal-600 bg-clip-text text-transparent group-hover:from-cyan-500 group-hover:to-teal-500 transition-all">
                DocuSearch
              </span>
            </button>

            {/* Search Box */}
            <div className="flex-1 max-w-3xl">
              <div className="relative">
                <div className="flex items-center border border-gray-300 rounded-full hover:shadow-md focus-within:shadow-md transition-shadow bg-white">
                  <svg className="w-5 h-5 text-gray-400 ml-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  <input
                    type="text"
                    className="flex-1 px-4 py-3 outline-none text-gray-700 bg-transparent"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={handleKeyPress}
                    placeholder="Tìm kiếm..."
                  />
                  {query && (
                    <button
                      onClick={() => setQuery("")}
                      className="mr-4 text-gray-400 hover:text-gray-600"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  )}
                  <button
                    onClick={handleSearch}
                    disabled={loading || !query.trim()}
                    className="mr-2 px-6 py-2 bg-gradient-to-r from-cyan-500 to-teal-500 text-white font-medium rounded-full hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? "Đang tìm..." : "Tìm"}
                  </button>
                </div>
              </div>
            </div>

            {/* Advanced Toggle */}
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center gap-2 text-gray-600 hover:text-cyan-600 transition-colors text-sm font-medium"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
              </svg>
              Nâng cao
            </button>
          </div>

          {/* Advanced Parameters Panel */}
          {showAdvanced && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">B Parameter</label>
                  <input
                    aria-label="B Parameter"
                    type="number"
                    step="0.05"
                    value={bParam}
                    onChange={(e) => setBParam(parseFloat(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">K1 Parameter</label>
                  <input
                    aria-label="K1 Parameter"
                    type="number"
                    step="0.1"
                    value={k1Param}
                    onChange={(e) => setK1Param(parseFloat(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Title Boost</label>
                  <input
                    aria-label="Title Boost"
                    type="number"
                    step="0.1"
                    value={titleBoost}
                    onChange={(e) => setTitleBoost(parseFloat(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Content Boost</label>
                  <input
                    aria-label="Content Boost"
                    type="number"
                    step="0.1"
                    value={contentBoost}
                    onChange={(e) => setContentBoost(parseFloat(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Result Limit</label>
                  <input
                    aria-label="Result Limit"
                    type="number"
                    step="10"
                    value={resultLimit}
                    onChange={(e) => setResultLimit(parseInt(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
                  />
                </div>
                <div className="flex items-end">
                  <button
                    onClick={resetAdvanced}
                    className="w-full px-4 py-2 bg-white border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                  >
                    Đặt lại mặc định
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-6">
        {/* Error Message */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center gap-3">
              <svg className="w-6 h-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-red-700">{error}</p>
            </div>
          </div>
        )}

        {/* Results Header */}
        {!loading && displayResults.length > 0 && (
          <div className="mb-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-4">
              <div className="text-gray-600">
                <p className="text-sm">
                  Tìm thấy khoảng <span className="font-semibold text-gray-900">{displayResults.length.toLocaleString()}</span> kết quả
                  {searchTime > 0 && (
                    <span className="ml-2">
                      ({searchTime.toFixed(2)} giây)
                    </span>
                  )}
                </p>
              </div>
              
              <div className="flex gap-2">
                <button
                  onClick={() => setSortBy("relevance")}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    sortBy === "relevance"
                      ? "bg-cyan-600 text-white shadow-md"
                      : "bg-white text-gray-700 hover:bg-gray-50 border border-gray-200"
                  }`}
                >
                  Liên quan
                </button>
                <button
                  onClick={() => setSortBy("pagerank")}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    sortBy === "pagerank"
                      ? "bg-cyan-600 text-white shadow-md"
                      : "bg-white text-gray-700 hover:bg-gray-50 border border-gray-200"
                  }`}
                >
                  PageRank
                </button>
                <button
                  onClick={() => setSortBy("title")}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    sortBy === "title"
                      ? "bg-cyan-600 text-white shadow-md"
                      : "bg-white text-gray-700 hover:bg-gray-50 border border-gray-200"
                  }`}
                >
                  Tiêu đề
                </button>
              </div>
            </div>
            
            <div className="h-px bg-gray-200"></div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="relative w-16 h-16 mx-auto mb-4">
                <div className="absolute inset-0 border-4 border-gray-200 rounded-full"></div>
                <div className="absolute inset-0 border-4 border-transparent border-t-cyan-600 rounded-full animate-spin"></div>
              </div>
              <p className="text-gray-600">Đang tìm kiếm...</p>
            </div>
          </div>
        )}

        {/* Results */}
        {!loading && displayResults.length > 0 && (
          <div className="space-y-6">
            {displayResults.map((result, index) => (
              <div
                key={result.doc_id}
                className="group bg-white rounded-lg hover:shadow-md transition-shadow duration-200"
                style={{
                  animationDelay: `${index * 50}ms`,
                  animation: "fadeInUp 0.3s ease-out forwards",
                }}
              >
                <div className="p-5">
                  <div className="flex gap-4">
                    {/* Image */}
                    {result.image_url && (
                      <div className="flex-shrink-0 w-28 h-28">
                        <img
                          src={result.image_url}
                          alt={result.title}
                          className="w-full h-full object-cover rounded-lg border border-gray-200"
                          onError={(e) => {
                            const target = e.target as HTMLImageElement;
                            target.style.display = 'none';
                          }}
                        />
                      </div>
                    )}

                    <div className="flex-1 min-w-0">
                      {/* URL */}
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs text-gray-600 truncate">
                          {new URL(result.url).hostname}
                        </span>
                      </div>

                      {/* Title */}
                      <Link
                        href={result.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="group/link"
                      >
                        <h3 
                          className="text-xl text-cyan-700 group-hover/link:underline mb-2 font-medium"
                          dangerouslySetInnerHTML={{ __html: highlightText(result.title, initialQuery) }}
                        />
                      </Link>

                      {/* Snippet */}
                      <p 
                        className="text-sm text-gray-600 leading-relaxed mb-3 line-clamp-2"
                        dangerouslySetInnerHTML={{ __html: highlightText(result.snippet, initialQuery) }}
                      />

                      {/* Metadata */}
                      <div className="flex flex-wrap items-center gap-3 text-xs">
                        <span className="inline-flex items-center px-2 py-1 rounded bg-cyan-50 text-cyan-700 font-medium">
                          <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                          </svg>
                          {result.relevance_percentage.toFixed(1)}%
                        </span>
                        
                        <span className="text-gray-500">
                          Score: {result.score.toFixed(2)}
                        </span>
                        
                        {result.pagerank_score && (
                          <span className="text-gray-500">
                            PR: {result.pagerank_score.toFixed(6)}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Empty State */}
        {!loading && displayResults.length === 0 && !error && (
          <div className="text-center py-20">
            <div className="inline-flex items-center justify-center w-20 h-20 bg-gray-100 rounded-full mb-6">
              <svg className="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Không tìm thấy kết quả</h3>
            <p className="text-gray-600">Thử tìm kiếm với từ khóa khác hoặc điều chỉnh tham số tìm kiếm</p>
          </div>
        )}
      </main>

      {/* Custom CSS for animations */}
      <style jsx>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        mark {
          background-color: rgb(254 243 199);
          padding: 0 0.125rem;
          border-radius: 0.125rem;
          font-weight: 600;
        }

        .line-clamp-2 {
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }
      `}</style>
    </div>
  );
}