import { useState, useEffect, useCallback, useRef } from 'react';
import type { PostItem, StatsOverview, ScrapeProgress, SettingsData, FilterState } from './types';
import { api } from './services/api';
import { Navbar } from './components/Navbar';
import { StatsCards } from './components/StatsCards';
import { SubredditConfig } from './components/SubredditConfig';
import { TREND_POD_US } from './presets';
import { PostTable } from './components/PostTable';
import { PostCardGrid } from './components/PostCardGrid';
import { CookieModal } from './components/CookieModal';
import { ScrapeConsole } from './components/ScrapeConsole';
import { TrendBoard } from './components/TrendBoard';
import { Search, LayoutGrid, List, SlidersHorizontal, Inbox, Newspaper, Wand2 } from 'lucide-react';

export function App() {
  const [posts, setPosts] = useState<PostItem[]>([]);
  const [stats, setStats] = useState<StatsOverview>({
    total_posts: 0,
    max_velocity: 0,
    top_subreddit: 'N/A',
    total_upvotes: 0,
    total_comments: 0,
    avg_velocity: 0,
  });

  const [settings, setSettings] = useState<SettingsData>({
    subreddits: [...TREND_POD_US],
    has_cookie: false,
    masked_cookie: '',
    categories: [
      { id: 'rising', name: 'Rising', description: 'Bắt trend sớm', path: 'rising/' },
      { id: 'top_day', name: 'Top (24h)', description: 'Nóng trong ngày', path: 'top/?sort=top&t=day' },
    ],
  });

  const [selectedCategories, setSelectedCategories] = useState<string[]>(['rising', 'top_day']);
  const [progress, setProgress] = useState<ScrapeProgress>({
    is_running: false,
    current_step: 'Sẵn sàng',
    current_subreddit: null,
    current_category: null,
    completed_requests: 0,
    total_requests: 0,
    scraped_count: 0,
    logs: [],
  });

  const [filters, setFilters] = useState<FilterState>({
    search: '',
    subreddit: 'all',
    sortBy: 'velocity_score',
    sortOrder: 'desc',
    viewMode: 'table',
  });

  const [activeTab, setActiveTab] = useState<'posts' | 'trends'>('posts');
  const [isCookieModalOpen, setIsCookieModalOpen] = useState(false);
  const wasRunningRef = useRef(false);

  // Tải dữ liệu ban đầu
  const loadInitialData = useCallback(async () => {
    try {
      const [fetchedPosts, fetchedStats, fetchedSettings] = await Promise.all([
        api.getPosts(),
        api.getStats(),
        api.getSettings(),
      ]);
      setPosts(fetchedPosts);
      setStats(fetchedStats);
      setSettings(fetchedSettings);
    } catch (err) {
      console.error('Lỗi khi tải dữ liệu khởi tạo:', err);
    }
  }, []);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  // Tải bài viết theo bộ lọc
  const refreshFilteredPosts = useCallback(async () => {
    try {
      const data = await api.getPosts({
        search: filters.search,
        subreddit: filters.subreddit,
        sortBy: filters.sortBy,
        sortOrder: filters.sortOrder,
      });
      setPosts(data);
      const s = await api.getStats();
      setStats(s);
    } catch (err) {
      console.error('Lỗi khi lọc bài viết:', err);
    }
  }, [filters]);

  useEffect(() => {
    refreshFilteredPosts();
  }, [refreshFilteredPosts]);

  // Lấy trạng thái cào 1 lần khi mở trang (để biết có phiên cào đang chạy không)
  useEffect(() => {
    api.getScrapeStatus().then(setProgress).catch(() => {});
  }, []);

  // Polling trạng thái CHỈ khi đang cào; dừng khi phiên cào kết thúc
  useEffect(() => {
    if (!progress.is_running) return;
    wasRunningRef.current = true;
    const timer = setInterval(async () => {
      try {
        const status = await api.getScrapeStatus();
        setProgress(status);

        // Khi vừa kết thúc cào dữ liệu, tự động làm mới bảng bài viết
        if (wasRunningRef.current && !status.is_running) {
          refreshFilteredPosts();
        }
        wasRunningRef.current = status.is_running;
      } catch {
        // bỏ qua lỗi polling mạng tạm thời
      }
    }, 1200);

    return () => clearInterval(timer);
  }, [progress.is_running, refreshFilteredPosts]);

  // Xử lý các sự kiện thao tác
  const handleStartScrape = async () => {
    try {
      await api.startScrape({
        subreddits: settings.subreddits,
        categories: selectedCategories,
        delay_min: 2.0,
        delay_max: 4.0,
      });
      const s = await api.getScrapeStatus();
      setProgress(s);
    } catch (err: unknown) {
      alert((err as Error).message || 'Không thể bắt đầu cào');
    }
  };

  const handleCancelScrape = async () => {
    try {
      await api.cancelScrape();
    } catch (err: unknown) {
      console.error('Lỗi hủy:', err);
    }
  };

  const handleSaveCookie = async (val: string) => {
    const updated = await api.updateCookie(val);
    setSettings((prev) => ({
      ...prev,
      has_cookie: updated.has_cookie,
      masked_cookie: updated.masked_cookie,
    }));
  };

  const handleDeleteCookie = async () => {
    await api.deleteCookie();
    setSettings((prev) => ({
      ...prev,
      has_cookie: false,
      masked_cookie: '',
    }));
  };

  const handleSubredditsChange = async (newSubs: string[]) => {
    setSettings((prev) => ({ ...prev, subreddits: newSubs }));
    try {
      await api.updateSubreddits(newSubs);
    } catch (err) {
      console.error('Lỗi lưu subreddits:', err);
    }
  };

  // Danh sách các subreddit độc nhất để đưa vào dropdown lọc
  const uniqueSubreddits = Array.from(new Set(posts.map((p) => p.subreddit)));

  return (
    <div className="app-container">
      {/* 1. Header Navigation */}
      <Navbar
        hasCookie={settings.has_cookie}
        maskedCookie={settings.masked_cookie}
        onOpenCookieModal={() => setIsCookieModalOpen(true)}
        onStartScrape={handleStartScrape}
        onCancelScrape={handleCancelScrape}
        isRunning={progress.is_running}
        onRefresh={refreshFilteredPosts}
        exportUrl={api.getExportUrl()}
      />

      {/* 2. Thống kê nhanh các chỉ số Trend */}
      <StatsCards stats={stats} />

      {/* 3. Bảng cấu hình Subreddit và Nguồn cào */}
      <SubredditConfig
        subreddits={settings.subreddits}
        onSubredditsChange={handleSubredditsChange}
        selectedCategories={selectedCategories}
        onCategoriesChange={setSelectedCategories}
        categories={settings.categories}
      />

      {/* Tab chuyển: Bài viết | Trend → POD */}
      <div className="main-tabs" role="tablist">
        <button
          role="tab"
          aria-selected={activeTab === 'posts'}
          className={`main-tab ${activeTab === 'posts' ? 'active' : ''}`}
          onClick={() => setActiveTab('posts')}
        >
          <Newspaper size={15} />
          <span>Bài viết</span>
        </button>
        <button
          role="tab"
          aria-selected={activeTab === 'trends'}
          className={`main-tab ${activeTab === 'trends' ? 'active' : ''}`}
          onClick={() => setActiveTab('trends')}
        >
          <Wand2 size={15} />
          <span>Trend → POD</span>
        </button>
      </div>

      {activeTab === 'trends' ? (
        <TrendBoard />
      ) : (
      <>
      {/* 4. Thanh tìm kiếm, phân loại và chuyển chế độ xem */}
      <div className="filter-bar">
        <div className="filter-left">
          <div className="search-box">
            <Search className="search-icon" size={16} />
            <input
              type="text"
              className="search-input"
              placeholder="Tìm kiếm bài viết theo từ khóa..."
              value={filters.search}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            />
          </div>

          <select
            className="select-dropdown"
            value={filters.subreddit}
            onChange={(e) => setFilters({ ...filters, subreddit: e.target.value })}
          >
            <option value="all">Tất cả Subreddit ({posts.length})</option>
            {uniqueSubreddits.map((sub) => (
              <option key={sub} value={sub}>
                r/{sub}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-right">
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <SlidersHorizontal size={14} color="var(--text-muted)" />
            <select
              className="select-dropdown"
              value={filters.sortBy}
              onChange={(e) =>
                setFilters({
                  ...filters,
                  sortBy: e.target.value as FilterState['sortBy'],
                })
              }
            >
              <option value="velocity_score">Sắp xếp: Velocity Score (Độ lan truyền)</option>
              <option value="score">Sắp xếp: Điểm Upvotes cao nhất</option>
              <option value="comments">Sắp xếp: Nhiều bình luận nhất</option>
              <option value="hours_since_posted">Sắp xếp: Bài mới đăng nhất</option>
            </select>
          </div>

          {/* Toggle View Mode: Bảng dữ liệu vs Thẻ trực quan */}
          <div className="view-switch">
            <button
              className={`view-btn ${filters.viewMode === 'table' ? 'active' : ''}`}
              onClick={() => setFilters({ ...filters, viewMode: 'table' })}
              title="Chế độ Bảng phân tích chi tiết"
            >
              <List size={16} />
            </button>
            <button
              className={`view-btn ${filters.viewMode === 'cards' ? 'active' : ''}`}
              onClick={() => setFilters({ ...filters, viewMode: 'cards' })}
              title="Chế độ Thẻ bài trực quan"
            >
              <LayoutGrid size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* 5. Vùng hiển thị dữ liệu bài viết */}
      {posts.length === 0 ? (
        <div className="empty-state">
          <Inbox size={42} color="var(--text-muted)" />
          <h3 className="empty-title">Chưa có bài viết nào phù hợp bộ lọc</h3>
          <p style={{ maxWidth: '420px', margin: '0 auto 16px', fontSize: '0.875rem' }}>
            Hãy bấm "Cào dữ liệu ngay" để quét bài viết mới nhất từ các subreddit đang chọn, hoặc thử xóa bộ lọc tìm kiếm.
          </p>
          <button className="btn btn-primary" onClick={handleStartScrape} disabled={progress.is_running}>
            Bắt đầu cào dữ liệu ngay
          </button>
        </div>
      ) : filters.viewMode === 'table' ? (
        <PostTable posts={posts} />
      ) : (
        <PostCardGrid posts={posts} />
      )}
      </>
      )}

      {/* 6. Console hiển thị nhật ký & thanh tiến trình thời gian thực */}
      <ScrapeConsole progress={progress} />

      {/* 7. Modal cài đặt Cookie Reddit */}
      <CookieModal
        isOpen={isCookieModalOpen}
        onClose={() => setIsCookieModalOpen(false)}
        hasCookie={settings.has_cookie}
        maskedCookie={settings.masked_cookie}
        onSaveCookie={handleSaveCookie}
        onDeleteCookie={handleDeleteCookie}
      />
    </div>
  );
}

export default App;
