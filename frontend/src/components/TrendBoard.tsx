import React, { useCallback, useEffect, useState } from 'react';
import type { TrendItem, DesignConcept } from '../types';
import { api } from '../services/api';
import {
  Radar, Download, Wand2, Loader2, Copy, Check, ShieldAlert, ShieldCheck,
  ChevronDown, ChevronUp, ExternalLink, Users, CalendarClock, Package, AlertTriangle,
  TrendingUp, TrendingDown,
} from 'lucide-react';

const TYPE_LABELS: Record<string, string> = {
  event: 'Sự kiện', sports: 'Thể thao', movie_tv: 'Phim/TV', music: 'Âm nhạc',
  gaming: 'Game', meme: 'Meme', seasonal: 'Mùa/Lễ', social: 'Xã hội',
  product: 'Sản phẩm', news: 'Tin tức', other: 'Khác',
};

const RISK_LABELS: Record<string, string> = {
  low: 'Rủi ro IP thấp', medium: 'Rủi ro IP trung bình', high: 'Rủi ro IP cao',
};

const ConceptCard: React.FC<{ concept: DesignConcept }> = ({ concept }) => {
  const [copied, setCopied] = useState(false);

  const copyPrompt = () => {
    navigator.clipboard.writeText(concept.designer_prompt);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="concept-card">
      <div className="concept-head">
        <span className="concept-name">{concept.concept_name}</span>
        <span className="concept-products">{concept.product_types.join(' · ')}</span>
      </div>

      {concept.text_on_design && <div className="concept-slogan">“{concept.text_on_design}”</div>}

      <p className="concept-text">{concept.visual_description}</p>

      <div className="concept-meta">
        <span><b>Phong cách:</b> {concept.style}</span>
        <span><b>Màu:</b> {concept.color_palette.join(', ')}</span>
      </div>

      <div className="prompt-box">
        <div className="prompt-box-head">
          <span>Prompt cho designer</span>
          <button className="btn btn-secondary btn-xs" onClick={copyPrompt}>
            {copied ? <Check size={13} /> : <Copy size={13} />}
            <span>{copied ? 'Đã copy' : 'Copy prompt'}</span>
          </button>
        </div>
        <pre className="prompt-text">{concept.designer_prompt}</pre>
      </div>

      <div className="keyword-row">
        {concept.target_keywords.map((k) => (
          <span key={k} className="keyword-chip">{k}</span>
        ))}
      </div>
    </div>
  );
};

const lastSeenOf = (t: TrendItem) => t.last_seen || t.detected_at || '';

const formatAgo = (iso: string) => {
  const hours = (Date.now() - new Date(iso).getTime()) / 3_600_000;
  if (!isFinite(hours)) return '';
  if (hours < 1) return `${Math.max(1, Math.round(hours * 60))} phút trước`;
  if (hours < 24) return `${Math.round(hours)}h trước`;
  return `${Math.round(hours / 24)} ngày trước`;
};

/** Nhãn trạng thái: Mới / Đang lên / Đang giảm / Chưa thấy lại */
const TrendStatusBadge: React.FC<{ trend: TrendItem; latest: string }> = ({ trend, latest }) => {
  const lastSeen = lastSeenOf(trend);
  if (lastSeen !== latest) {
    return (
      <span className="trend-status status-stale" title="Trend không xuất hiện ở lần phát hiện gần nhất">
        Chưa thấy lại · {formatAgo(lastSeen)}
      </span>
    );
  }
  if ((trend.first_seen || lastSeen) === lastSeen && trend.prev_score == null) {
    return <span className="trend-status status-new">Mới</span>;
  }
  const prev = trend.prev_score ?? 0;
  if (prev > 0 && trend.trend_score > prev * 1.1) {
    return (
      <span className="trend-status status-up" title={`Điểm lần trước: ${Math.round(prev).toLocaleString()}`}>
        <TrendingUp size={12} /> Đang lên
      </span>
    );
  }
  if (prev > 0 && trend.trend_score < prev * 0.9) {
    return (
      <span className="trend-status status-down" title={`Điểm lần trước: ${Math.round(prev).toLocaleString()}`}>
        <TrendingDown size={12} /> Đang giảm
      </span>
    );
  }
  return null;
};

const TrendCard: React.FC<{
  trend: TrendItem;
  rank: number;
  latest: string;
  isGenerating: boolean;
  anyGenerating: boolean;
  onGenerate: (id: string) => void;
}> = ({ trend, rank, latest, isGenerating, anyGenerating, onGenerate }) => {
  const [showSources, setShowSources] = useState(false);
  const [showIdeas, setShowIdeas] = useState(true);
  const ideas = trend.ideas;

  return (
    <article className={`trend-card ${trend.is_pod_friendly ? '' : 'trend-card-muted'}`}>
      <div className="trend-card-top">
        <div>
          <div className="trend-name-row">
            <span className="trend-rank tabular-nums">#{rank}</span>
            <h3 className="trend-name">{trend.name}</h3>
            <span className="sub-pill">{TYPE_LABELS[trend.trend_type] ?? trend.trend_type}</span>
            <TrendStatusBadge trend={trend} latest={latest} />
            {!trend.is_pod_friendly && <span className="trend-flag">Không hợp POD</span>}
          </div>
          <div className="trend-keyword">{trend.keyword_en}</div>
        </div>

        <div
          className="trend-score tabular-nums"
          title="Điểm ở lần thấy gần nhất = tổng velocity các bài × số subreddit khác nhau cùng nhắc tới"
        >
          <span className="trend-score-value">{Math.round(trend.trend_score).toLocaleString()}</span>
          <span className="trend-score-label">
            {trend.post_count} bài · {trend.subreddits.length} sub
          </span>
        </div>
      </div>

      <p className="trend-summary">{trend.summary}</p>
      <p className="trend-reason">
        <b>{trend.is_pod_friendly ? 'Vì sao hợp POD:' : 'Vì sao không hợp:'}</b> {trend.pod_reason}
      </p>

      <div className="trend-actions">
        <button className="btn btn-primary" disabled={anyGenerating} onClick={() => onGenerate(trend.trend_id)}>
          {isGenerating ? <Loader2 size={15} className="spin" /> : <Wand2 size={15} />}
          <span>{isGenerating ? 'Đang phân tích...' : ideas ? 'Tạo lại ý tưởng' : 'Tạo ý tưởng POD'}</span>
        </button>
        <button className="btn btn-secondary" onClick={() => setShowSources((v) => !v)}>
          {showSources ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
          <span>Bài nguồn ({trend.posts.length})</span>
        </button>
        {ideas && (
          <button className="btn btn-secondary" onClick={() => setShowIdeas((v) => !v)}>
            {showIdeas ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
            <span>{showIdeas ? 'Ẩn ý tưởng' : 'Xem ý tưởng'}</span>
          </button>
        )}
      </div>

      {showSources && (
        <ul className="trend-sources">
          {trend.posts.map((p) => (
            <li key={p.post_id}>
              <span className="sub-pill">r/{p.subreddit}</span>
              <a href={p.url} target="_blank" rel="noreferrer" className="post-title-link">
                {p.title} <ExternalLink size={12} />
              </a>
              <span className="trend-source-meta tabular-nums">
                {p.score.toLocaleString()}↑ · {p.comments.toLocaleString()} cmt
              </span>
            </li>
          ))}
        </ul>
      )}

      {ideas && showIdeas && (
        <div className="ideas-section">
          <div className="ideas-overview">
            <div className="ideas-overview-item">
              <Users size={15} />
              <div><b>Khách hàng</b><p>{ideas.audience}</p></div>
            </div>
            <div className="ideas-overview-item">
              <CalendarClock size={15} />
              <div><b>Thời điểm</b><p>{ideas.peak_window}</p></div>
            </div>
            <div className="ideas-overview-item">
              <Package size={15} />
              <div><b>Sản phẩm phù hợp</b><p>{ideas.best_products.join(', ')}</p></div>
            </div>
          </div>

          <div className={`risk-box risk-${ideas.ip_risk.level}`}>
            <div className="risk-head">
              {ideas.ip_risk.level === 'low' ? <ShieldCheck size={16} /> : <ShieldAlert size={16} />}
              <b>{RISK_LABELS[ideas.ip_risk.level]}</b>
            </div>
            <p>{ideas.ip_risk.explanation}</p>
            {ideas.ip_risk.avoid.length > 0 && (
              <p><b>Tránh:</b> {ideas.ip_risk.avoid.join(', ')}</p>
            )}
            {ideas.ip_risk.safe_alternatives.length > 0 && (
              <p><b>Thay bằng:</b> {ideas.ip_risk.safe_alternatives.join(', ')}</p>
            )}
          </div>

          <div className="concepts-grid">
            {ideas.design_concepts.map((c, i) => (
              <ConceptCard key={`${trend.trend_id}-${i}`} concept={c} />
            ))}
          </div>
        </div>
      )}
    </article>
  );
};

export const TrendBoard: React.FC = () => {
  const [trends, setTrends] = useState<TrendItem[]>([]);
  const [llmConfigured, setLlmConfigured] = useState(true);
  const [model, setModel] = useState('');
  const [detecting, setDetecting] = useState(false);
  const [generatingId, setGeneratingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [onlyPod, setOnlyPod] = useState(true);

  const load = useCallback(async () => {
    try {
      const data = await api.getTrends();
      setTrends(data.trends);
      setLlmConfigured(data.llm_configured);
      setModel(data.model);
    } catch (err) {
      setError((err as Error).message);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleDetect = async () => {
    setDetecting(true);
    setError(null);
    try {
      setTrends(await api.detectTrends());
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setDetecting(false);
    }
  };

  const handleGenerate = async (trendId: string) => {
    setGeneratingId(trendId);
    setError(null);
    try {
      const updated = await api.generateIdeas(trendId);
      setTrends((prev) => prev.map((t) => (t.trend_id === trendId ? updated : t)));
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setGeneratingId(null);
    }
  };

  const visible = onlyPod ? trends.filter((t) => t.is_pod_friendly) : trends;
  const hiddenCount = trends.length - visible.length;
  const hasIdeas = trends.some((t) => t.ideas);
  const latest = trends.reduce((max, t) => (lastSeenOf(t) > max ? lastSeenOf(t) : max), '');
  const freshCount = trends.filter((t) => lastSeenOf(t) === latest).length;

  return (
    <section className="trend-board">
      <div className="config-panel">
        <div className="panel-header">
          <div className="panel-title">
            <Radar size={18} color="#38bdf8" />
            <span>Trend → Ý tưởng sản phẩm POD (thị trường Mỹ)</span>
          </div>
          <div className="trend-toolbar">
            <label className="checkbox-label">
              <input type="checkbox" checked={onlyPod} onChange={(e) => setOnlyPod(e.target.checked)} />
              <span>Chỉ trend hợp POD{hiddenCount > 0 ? ` (ẩn ${hiddenCount})` : ''}</span>
            </label>
            {hasIdeas && (
              <a className="btn btn-secondary" href={api.getIdeasExportUrl()}>
                <Download size={15} />
                <span>Xuất CSV cho designer</span>
              </a>
            )}
            <button className="btn btn-primary" onClick={handleDetect} disabled={detecting || !llmConfigured}>
              {detecting ? <Loader2 size={15} className="spin" /> : <Radar size={15} />}
              <span>{detecting ? 'Đang gom trend...' : 'Phát hiện trend'}</span>
            </button>
          </div>
        </div>
        <p className="trend-hint">
          Bước 1: cào dữ liệu (nên dùng preset <b>Trend POD Mỹ</b>) ở tab Bài viết. Bước 2: bấm <b>Phát hiện trend</b>.
          Bước 3: chọn trend và bấm <b>Tạo ý tưởng POD</b>. Model: <code>{model}</code>
        </p>
        {trends.length > 0 && (
          <p className="trend-hint">
            Đang lưu <b>{trends.length}</b> trend (giữ tối đa 3 ngày) · lần phát hiện gần nhất{' '}
            <b>{latest ? new Date(latest).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }) : '—'}</b>{' '}
            tìm thấy <b>{freshCount}</b> trend. Mỗi lần phát hiện chỉ phân tích các subreddit đang chọn; trend của mảng khác vẫn được giữ.
          </p>
        )}

        {!llmConfigured && (
          <div className="trend-alert">
            <AlertTriangle size={16} />
            <span>
              Chưa cấu hình <code>OPENAI_API_KEY</code>. Tạo file <code>.env</code> ở thư mục dự án với dòng{' '}
              <code>OPENAI_API_KEY=sk-...</code> rồi khởi động lại ứng dụng.
            </span>
          </div>
        )}
        {error && (
          <div className="trend-alert">
            <AlertTriangle size={16} />
            <span>{error}</span>
          </div>
        )}
      </div>

      {visible.length === 0 ? (
        <div className="empty-state">
          <Radar size={42} color="var(--text-muted)" />
          <h3 className="empty-title">Chưa có trend nào</h3>
          <p style={{ maxWidth: '440px', margin: '0 auto', fontSize: '0.875rem' }}>
            Hãy cào dữ liệu từ các subreddit đại chúng rồi bấm "Phát hiện trend" để AI gom các bài thành chủ đề.
          </p>
        </div>
      ) : (
        <div className="trend-list">
          {visible.map((t, i) => (
            <TrendCard
              key={t.trend_id}
              trend={t}
              rank={i + 1}
              latest={latest}
              isGenerating={generatingId === t.trend_id}
              anyGenerating={generatingId !== null}
              onGenerate={handleGenerate}
            />
          ))}
        </div>
      )}
    </section>
  );
};
