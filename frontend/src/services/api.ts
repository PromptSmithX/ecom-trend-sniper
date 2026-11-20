import type { PostItem, StatsOverview, ScrapeProgress, SettingsData, TrendItem, TrendsResponse } from '../types';

const API_BASE = '/api';

export const api = {
  async getPosts(params?: {
    search?: string;
    subreddit?: string;
    sortBy?: string;
    sortOrder?: string;
    limit?: number;
  }): Promise<PostItem[]> {
    const q = new URLSearchParams();
    if (params?.search) q.set('search', params.search);
    if (params?.subreddit && params.subreddit !== 'all') q.set('subreddit', params.subreddit);
    if (params?.sortBy) q.set('sort_by', params.sortBy);
    if (params?.sortOrder) q.set('sort_order', params.sortOrder);
    if (params?.limit) q.set('limit', String(params.limit));

    const res = await fetch(`${API_BASE}/posts?${q.toString()}`);
    if (!res.ok) throw new Error('Không thể tải danh sách bài viết');
    return res.json();
  },

  async getStats(): Promise<StatsOverview> {
    const res = await fetch(`${API_BASE}/posts/stats`);
    if (!res.ok) throw new Error('Không thể tải thông số thống kê');
    return res.json();
  },

  async getSettings(): Promise<SettingsData> {
    const res = await fetch(`${API_BASE}/settings`);
    if (!res.ok) throw new Error('Không thể tải cài đặt');
    return res.json();
  },

  async updateCookie(cookie: string): Promise<{ has_cookie: boolean; masked_cookie: string }> {
    const res = await fetch(`${API_BASE}/settings/cookie`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reddit_session: cookie }),
    });
    if (!res.ok) throw new Error('Cập nhật cookie thất bại');
    return res.json();
  },

  async deleteCookie(): Promise<void> {
    const res = await fetch(`${API_BASE}/settings/cookie`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Xóa cookie thất bại');
  },

  async updateSubreddits(subreddits: string[]): Promise<{ subreddits: string[] }> {
    const res = await fetch(`${API_BASE}/settings/subreddits`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(subreddits),
    });
    if (!res.ok) throw new Error('Lưu danh sách subreddit thất bại');
    return res.json();
  },

  async startScrape(payload: {
    subreddits: string[];
    categories: string[];
    delay_min?: number;
    delay_max?: number;
    cookie?: string;
  }): Promise<{ message: string }> {
    const res = await fetch(`${API_BASE}/scrape/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Không thể bắt đầu tác vụ cào');
    }
    return res.json();
  },

  async getScrapeStatus(): Promise<ScrapeProgress> {
    const res = await fetch(`${API_BASE}/scrape/status`);
    if (!res.ok) throw new Error('Không thể lấy trạng thái cào');
    return res.json();
  },

  async cancelScrape(): Promise<void> {
    await fetch(`${API_BASE}/scrape/cancel`, { method: 'POST' });
  },

  async clearPosts(): Promise<void> {
    const res = await fetch(`${API_BASE}/posts/clear`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Không thể xóa bài viết');
  },

  getExportUrl(): string {
    return `${API_BASE}/posts/export`;
  },

  // ---------------- Trend → POD ----------------
  async getTrends(): Promise<TrendsResponse> {
    const res = await fetch(`${API_BASE}/trends`);
    if (!res.ok) throw new Error('Không thể tải danh sách trend');
    return res.json();
  },

  async detectTrends(): Promise<TrendItem[]> {
    const res = await fetch(`${API_BASE}/trends/detect`, { method: 'POST' });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Phát hiện trend thất bại');
    }
    return (await res.json()).trends;
  },

  async generateIdeas(trendId: string): Promise<TrendItem> {
    const res = await fetch(`${API_BASE}/trends/${encodeURIComponent(trendId)}/ideas`, { method: 'POST' });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Tạo ý tưởng POD thất bại');
    }
    return res.json();
  },

  getIdeasExportUrl(): string {
    return `${API_BASE}/trends/export`;
  },
};
