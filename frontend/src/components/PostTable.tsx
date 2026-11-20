import React, { useState } from 'react';
import type { PostItem } from '../types';
import { ExternalLink, Copy, Check, ShieldCheck, Flame, Zap } from 'lucide-react';

interface PostTableProps {
  posts: PostItem[];
}

export const PostTable: React.FC<PostTableProps> = ({ posts }) => {
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const handleCopy = (url: string, id: string) => {
    navigator.clipboard.writeText(url);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const getVelocityClass = (score: number) => {
    if (score >= 50) return 'hot';
    if (score >= 20) return 'warm';
    return 'normal';
  };

  return (
    <div className="table-container">
      <table className="data-table">
        <thead>
          <tr>
            <th style={{ width: '60px' }}>Hạng</th>
            <th style={{ width: '150px' }}>Velocity Score</th>
            <th>Tiêu đề bài viết</th>
            <th style={{ width: '130px' }}>Cộng đồng</th>
            <th style={{ width: '100px' }}>Điểm Upvotes</th>
            <th style={{ width: '100px' }}>Bình luận</th>
            <th style={{ width: '110px' }}>Thời gian</th>
            <th style={{ width: '200px' }}>Thao tác truy cập</th>
          </tr>
        </thead>
        <tbody>
          {posts.map((post, idx) => {
            const velClass = getVelocityClass(post.velocity_score);
            const isCopied = copiedId === post.post_id;

            return (
              <tr key={post.post_id}>
                <td style={{ color: 'var(--text-muted)', fontWeight: 600 }}>#{idx + 1}</td>

                <td>
                  <span
                    className={`velocity-badge ${velClass} tabular-nums`}
                    title={`Công thức: (${post.score} + ${post.comments}*2) / ${post.hours_since_posted}h`}
                  >
                    {velClass === 'hot' ? <Flame size={14} /> : <Zap size={14} />}
                    <span>{post.velocity_score.toFixed(1)}</span>
                  </span>
                </td>

                <td>
                  <a
                    href={post.url}
                    target="_blank"
                    rel="noreferrer"
                    className="post-title-link"
                    title="Bấm để mở trực tiếp trên old.reddit.com (Không bị chặn DNS ở VN)"
                  >
                    {post.title}
                  </a>
                </td>

                <td>
                  <span className="sub-pill">r/{post.subreddit}</span>
                </td>

                <td className="tabular-nums" style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                  {post.score.toLocaleString()}
                </td>

                <td className="tabular-nums" style={{ color: 'var(--text-secondary)' }}>
                  {post.comments.toLocaleString()}
                </td>

                <td className="tabular-nums" style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                  {post.hours_since_posted < 1
                    ? `${Math.round(post.hours_since_posted * 60)} phút`
                    : `${post.hours_since_posted.toFixed(1)} giờ`}
                </td>

                <td>
                  <div className="action-buttons-cell">
                    {/* Nút Cách 1: Mở thẳng old.reddit.com (Không bị chặn DNS) */}
                    <a
                      href={post.url}
                      target="_blank"
                      rel="noreferrer"
                      className="btn btn-accent-old"
                      style={{ padding: '5px 10px', fontSize: '0.775rem' }}
                      title="Mở bằng old.reddit.com (Cách 1: vượt rào cản DNS nhà mạng VN)"
                    >
                      <ShieldCheck size={13} />
                      <span>Mở old.reddit</span>
                      <ExternalLink size={12} />
                    </a>

                    {/* Nút Sao chép */}
                    <button
                      className="btn btn-secondary"
                      style={{ padding: '5px 8px' }}
                      onClick={() => handleCopy(post.url, post.post_id)}
                      title="Sao chép link bài viết"
                    >
                      {isCopied ? <Check size={13} color="#34d399" /> : <Copy size={13} />}
                    </button>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
