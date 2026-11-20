import React, { useState } from 'react';
import type { PostItem } from '../types';
import { ThumbsUp, MessageSquare, Clock, ExternalLink, Copy, Check, ShieldCheck, Flame, Zap } from 'lucide-react';

interface PostCardGridProps {
  posts: PostItem[];
}

export const PostCardGrid: React.FC<PostCardGridProps> = ({ posts }) => {
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
    <div className="cards-grid">
      {posts.map((post, idx) => {
        const velClass = getVelocityClass(post.velocity_score);
        const isCopied = copiedId === post.post_id;

        return (
          <article key={post.post_id} className="post-card">
            <div className="card-top">
              <span className="sub-pill">r/{post.subreddit}</span>
              <span
                className={`velocity-badge ${velClass} tabular-nums`}
                title={`Velocity = (${post.score} + ${post.comments}*2) / ${post.hours_since_posted}h`}
              >
                {velClass === 'hot' ? <Flame size={13} /> : <Zap size={13} />}
                <span>#{idx + 1} • {post.velocity_score.toFixed(1)}</span>
              </span>
            </div>

            <a
              href={post.url}
              target="_blank"
              rel="noreferrer"
              className="post-title-link card-title"
              title="Bấm để mở trực tiếp trên old.reddit.com"
            >
              {post.title}
            </a>

            <div className="card-meta-row">
              <span className="meta-item tabular-nums">
                <ThumbsUp size={14} color="#60a5fa" />
                <span>{post.score.toLocaleString()}</span>
              </span>

              <span className="meta-item tabular-nums">
                <MessageSquare size={14} color="#a78bfa" />
                <span>{post.comments.toLocaleString()}</span>
              </span>

              <span className="meta-item tabular-nums">
                <Clock size={14} color="var(--text-muted)" />
                <span>
                  {post.hours_since_posted < 1
                    ? `${Math.round(post.hours_since_posted * 60)}m trước`
                    : `${post.hours_since_posted.toFixed(1)}h trước`}
                </span>
              </span>
            </div>

            <div className="card-footer">
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Nguồn: {post.category === 'rising' ? 'Rising feed' : 'Top feed'}
              </span>

              <div style={{ display: 'flex', gap: '8px' }}>
                <a
                  href={post.url}
                  target="_blank"
                  rel="noreferrer"
                  className="btn btn-accent-old"
                  style={{ padding: '6px 12px', fontSize: '0.8rem' }}
                  title="Mở bằng old.reddit.com (Cách 1)"
                >
                  <ShieldCheck size={14} />
                  <span>Mở old.reddit</span>
                  <ExternalLink size={12} />
                </a>

                <button
                  className="btn btn-secondary"
                  style={{ padding: '6px 10px' }}
                  onClick={() => handleCopy(post.url, post.post_id)}
                  title="Sao chép link"
                >
                  {isCopied ? <Check size={14} color="#34d399" /> : <Copy size={14} />}
                </button>
              </div>
            </div>
          </article>
        );
      })}
    </div>
  );
};
