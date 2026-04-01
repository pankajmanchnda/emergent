import { useEffect, useState, useCallback } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import axios from "axios";
import { Radar, ArrowUpRight, Loader2, Radio, Youtube, Rss, RefreshCw, CheckCircle, AlertCircle, Clock } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Tag color mapping
const getTagClass = (tag) => {
  const tagLower = tag.toLowerCase();
  if (tagLower === 'war') return 'tag-war';
  if (tagLower === 'nuclear') return 'tag-nuclear';
  if (tagLower === 'diplomacy') return 'tag-diplomacy';
  if (tagLower === 'iran') return 'tag-iran';
  if (tagLower === 'israel') return 'tag-israel';
  if (tagLower === 'military') return 'tag-military';
  if (tagLower === 'sanctions') return 'tag-sanctions';
  if (tagLower === 'us') return 'tag-us';
  return 'tag-default';
};

// Format relative time
const formatRelativeTime = (dateString) => {
  const date = new Date(dateString);
  const now = new Date();
  const diffInSeconds = Math.floor((now - date) / 1000);

  if (diffInSeconds < 60) return 'Just now';
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
  if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)}d ago`;
  
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
};

// News Card Component
const NewsCard = ({ item }) => {
  return (
    <article className="news-card group" data-testid="news-card">
      <div>
        <div className="card-header">
          <div className="flex items-center gap-2">
            <span className="card-source">{item.source}</span>
            {item.item_type === 'youtube' ? (
              <span className="type-badge youtube">
                <Youtube size={10} />
                YT
              </span>
            ) : (
              <span className="type-badge">
                <Rss size={10} />
                RSS
              </span>
            )}
            {item.duration && item.item_type === 'youtube' && (
              <span className="duration-badge">
                <Clock size={10} />
                {item.duration}
              </span>
            )}
          </div>
          <span className="card-time">{formatRelativeTime(item.published_at)}</span>
        </div>
        
        <h3 className="card-title" data-testid="news-card-title">
          {item.title}
        </h3>
        
        {item.summary && (
          <p className="card-summary">{item.summary}</p>
        )}
      </div>
      
      <div className="card-footer">
        <div className="tags-container">
          {item.tags.map((tag, index) => (
            <span key={index} className={`tag ${getTagClass(tag)}`}>
              {tag}
            </span>
          ))}
        </div>
        
        <a
          href={item.url}
          target="_blank"
          rel="noopener noreferrer"
          className="card-link-icon"
          data-testid="news-card-link"
          aria-label="Open article"
        >
          <ArrowUpRight size={20} />
        </a>
      </div>
    </article>
  );
};

// Filter Button Component
const FilterButton = ({ label, isActive, onClick, testId }) => {
  return (
    <button
      className={`filter-btn ${isActive ? 'active' : ''}`}
      onClick={onClick}
      data-testid={testId}
    >
      {label}
    </button>
  );
};

// Refresh Button Component
const RefreshButton = ({ onClick, isRefreshing, lastResult }) => {
  return (
    <div className="refresh-container">
      <button
        className={`refresh-btn ${isRefreshing ? 'refreshing' : ''}`}
        onClick={onClick}
        disabled={isRefreshing}
        data-testid="refresh-btn"
      >
        <RefreshCw size={16} className={isRefreshing ? 'spin' : ''} />
        <span>{isRefreshing ? 'Fetching YouTube...' : 'Refresh Feed'}</span>
      </button>
      {lastResult && (
        <div className={`refresh-result ${lastResult.success ? 'success' : 'error'}`}>
          {lastResult.success ? <CheckCircle size={14} /> : <AlertCircle size={14} />}
          <span>{lastResult.message}</span>
        </div>
      )}
    </div>
  );
};

// Main Dashboard Component
const Dashboard = () => {
  const [newsItems, setNewsItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeFilter, setActiveFilter] = useState('all');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [refreshResult, setRefreshResult] = useState(null);

  const filters = [
    { key: 'all', label: 'All' },
    { key: 'iran', label: 'Iran' },
    { key: 'war', label: 'War' },
    { key: 'nuclear', label: 'Nuclear' },
    { key: 'diplomacy', label: 'Diplomacy' },
  ];

  const fetchNews = useCallback(async () => {
    setLoading(true);
    try {
      const params = activeFilter !== 'all' ? { tag: activeFilter } : {};
      const response = await axios.get(`${API}/news`, { params });
      setNewsItems(response.data);
    } catch (error) {
      console.error('Error fetching news:', error);
    } finally {
      setLoading(false);
    }
  }, [activeFilter]);

  useEffect(() => {
    fetchNews();
  }, [fetchNews]);

  const handleFilterClick = (filterKey) => {
    setActiveFilter(filterKey);
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    setRefreshResult(null);
    
    try {
      const response = await axios.post(`${API}/news/refresh`);
      setRefreshResult({
        success: true,
        message: `Added ${response.data.new_items} new items`
      });
      // Refresh the news list
      await fetchNews();
    } catch (error) {
      console.error('Error refreshing news:', error);
      setRefreshResult({
        success: false,
        message: error.response?.data?.detail || 'Failed to refresh'
      });
    } finally {
      setIsRefreshing(false);
      // Clear result after 5 seconds
      setTimeout(() => setRefreshResult(null), 5000);
    }
  };

  return (
    <div className="app-container" data-testid="dashboard">
      {/* Background layers */}
      <div className="tactical-bg" aria-hidden="true" />
      <div className="tactical-overlay" aria-hidden="true" />

      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <div className="logo">
            <Radar className="logo-icon" size={28} />
            <span>Iran War Monitor</span>
          </div>
          <div className="header-right">
            <div className="live-indicator">
              <Radio size={12} className="text-[#10B981] animate-pulse" />
              <span className="font-mono text-xs text-[#737373] uppercase tracking-wider">
                Live Feed
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="main-content">
        {/* Stats bar */}
        <div className="stats-bar">
          <div className="stat-item">
            <span>Total Items:</span>
            <span className="stat-value">{newsItems.length}</span>
          </div>
          <div className="stat-item">
            <span>Filter:</span>
            <span className="stat-value uppercase">{activeFilter}</span>
          </div>
          <div className="stat-item">
            <span>Sources:</span>
            <span className="stat-value">9 Channels</span>
          </div>
        </div>

        {/* Controls Row */}
        <div className="controls-row">
          {/* Filters */}
          <div className="filters-container">
            {filters.map((filter) => (
              <FilterButton
                key={filter.key}
                label={filter.label}
                isActive={activeFilter === filter.key}
                onClick={() => handleFilterClick(filter.key)}
                testId={`filter-btn-${filter.key}`}
              />
            ))}
          </div>

          {/* Refresh Button */}
          <RefreshButton 
            onClick={handleRefresh}
            isRefreshing={isRefreshing}
            lastResult={refreshResult}
          />
        </div>

        {/* News Grid */}
        <div className="news-grid">
          {loading ? (
            <div className="loading-container">
              <Loader2 className="loading-spinner" size={32} />
            </div>
          ) : newsItems.length === 0 ? (
            <div className="empty-state">
              <Radar className="empty-icon" size={48} />
              <h3 className="empty-title">No Intelligence Available</h3>
              <p className="empty-text">
                {activeFilter !== 'all' 
                  ? `No items found with tag "${activeFilter}"`
                  : 'Click "Refresh Feed" to fetch latest Iran war news from YouTube'}
              </p>
            </div>
          ) : (
            newsItems.map((item) => (
              <NewsCard key={item.id} item={item} />
            ))
          )}
        </div>
      </main>
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Dashboard />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
