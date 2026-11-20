import React from 'react';
import type { StatsOverview } from '../types';
import { Zap, Flame, MessageSquare, Compass } from 'lucide-react';

interface StatsCardsProps {
  stats: StatsOverview;
}

export const StatsCards: React.FC<StatsCardsProps> = ({ stats }) => {
  return (
    <section className="stats-grid">
      <div className="stat-card" style={{ '--stat-accent': '#3b82f6' } as React.CSSProperties}>
        <div className="stat-label">
          <Compass size={16} color="#60a5fa" />
          <span>Tổng số bài thu thập</span>
        </div>
        <div className="stat-value tabular-nums">{stats.total_posts.toLocaleString()}</div>
        <div className="stat-desc">Dữ liệu từ rising & top trong ngày</div>
      </div>

      <div className="stat-card" style={{ '--stat-accent': '#10b981' } as React.CSSProperties}>
        <div className="stat-label">
          <Zap size={16} color="#34d399" />
          <span>Velocity Score đỉnh</span>
        </div>
        <div className="stat-value tabular-nums">{stats.max_velocity.toFixed(1)}</div>
        <div className="stat-desc">Tốc độ lan truyền nóng nhất hiện tại</div>
      </div>

      <div className="stat-card" style={{ '--stat-accent': '#ff4500' } as React.CSSProperties}>
        <div className="stat-label">
          <Flame size={16} color="#ff6b35" />
          <span>Subreddit sôi động nhất</span>
        </div>
        <div className="stat-value" style={{ fontSize: '1.45rem' }}>
          r/{stats.top_subreddit}
        </div>
        <div className="stat-desc">Cộng đồng có mật độ thảo luận cao nhất</div>
      </div>

      <div className="stat-card" style={{ '--stat-accent': '#a855f7' } as React.CSSProperties}>
        <div className="stat-label">
          <MessageSquare size={16} color="#c084fc" />
          <span>Tổng lượng tương tác</span>
        </div>
        <div className="stat-value tabular-nums">
          {(stats.total_upvotes + stats.total_comments).toLocaleString()}
        </div>
        <div className="stat-desc">
          {stats.total_upvotes.toLocaleString()} upvotes + {stats.total_comments.toLocaleString()} comments
        </div>
      </div>
    </section>
  );
};
