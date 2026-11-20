export interface PostItem {
  post_id: string;
  subreddit: string;
  category: string;
  title: string;
  url: string;           // https://old.reddit.com (Cách 1)
  standard_url: string;  // https://www.reddit.com
  score: number;
  comments: number;
  created_utc: number;
  hours_since_posted: number;
  velocity_score: number;
}

export interface StatsOverview {
  total_posts: number;
  max_velocity: number;
  top_subreddit: string;
  total_upvotes: number;
  total_comments: number;
  avg_velocity: number;
}

export interface LogMessage {
  timestamp: string;
  level: 'info' | 'success' | 'warning' | 'error';
  message: string;
}

export interface ScrapeProgress {
  is_running: boolean;
  current_step: string;
  current_subreddit: string | null;
  current_category: string | null;
  completed_requests: number;
  total_requests: number;
  scraped_count: number;
  logs: LogMessage[];
}

export interface SettingsData {
  subreddits: string[];
  has_cookie: boolean;
  masked_cookie: string;
  categories: {
    id: string;
    name: string;
    description: string;
    path: string;
  }[];
}

export interface FilterState {
  search: string;
  subreddit: string;
  sortBy: 'velocity_score' | 'score' | 'comments' | 'hours_since_posted';
  sortOrder: 'desc' | 'asc';
  viewMode: 'table' | 'cards';
}

// ---------------- Trend → POD ----------------
export interface DesignConcept {
  concept_name: string;
  product_types: string[];
  text_on_design: string;
  visual_description: string;
  style: string;
  color_palette: string[];
  designer_prompt: string;
  target_keywords: string[];
}

export interface IpRisk {
  level: 'low' | 'medium' | 'high';
  explanation: string;
  avoid: string[];
  safe_alternatives: string[];
}

export interface PodIdeas {
  audience: string;
  peak_window: string;
  best_products: string[];
  design_concepts: DesignConcept[];
  ip_risk: IpRisk;
}

export interface TrendPost {
  post_id: string;
  title: string;
  subreddit: string;
  url: string;
  score: number;
  comments: number;
  velocity_score: number;
}

export interface TrendItem {
  trend_id: string;
  name: string;
  keyword_en: string;
  trend_type: string;
  summary: string;
  is_pod_friendly: boolean;
  pod_reason: string;
  post_ids: string[];
  posts: TrendPost[];
  subreddits: string[];
  post_count: number;
  total_velocity: number;
  trend_score: number;
  detected_at: string;
  first_seen?: string;
  last_seen?: string;
  prev_score?: number | null;
  ideas: PodIdeas | null;
  ideas_generated_at: string | null;
}

export interface TrendsResponse {
  trends: TrendItem[];
  llm_configured: boolean;
  model: string;
}
