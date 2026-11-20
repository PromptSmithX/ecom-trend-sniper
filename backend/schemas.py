# -*- coding: utf-8 -*-
"""
backend/schemas.py
------------------
Định nghĩa Pydantic Models cho request, response và data structure.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal

from backend.config import DEFAULT_SUBREDDITS


class PostItem(BaseModel):
    post_id: str
    subreddit: str
    category: str
    title: str
    url: str  # Đường dẫn old.reddit.com (Cách 1: Không bị chặn DNS)
    standard_url: str = ""  # Đường dẫn www.reddit.com chuẩn
    score: int = 0
    comments: int = 0
    created_utc: float
    hours_since_posted: float
    velocity_score: float


class ScrapeRequest(BaseModel):
    subreddits: List[str] = Field(default_factory=lambda: list(DEFAULT_SUBREDDITS))
    categories: List[str] = Field(default_factory=lambda: ["rising", "top_day"])
    delay_min: float = 2.0
    delay_max: float = 4.0
    cookie: Optional[str] = None


class LogMessage(BaseModel):
    timestamp: str
    level: str  # info, success, warning, error
    message: str


class ScrapeProgress(BaseModel):
    is_running: bool = False
    current_step: str = ""
    current_subreddit: Optional[str] = None
    current_category: Optional[str] = None
    completed_requests: int = 0
    total_requests: int = 0
    scraped_count: int = 0
    logs: List[LogMessage] = Field(default_factory=list)


class CookiePayload(BaseModel):
    reddit_session: str


class CookieStatus(BaseModel):
    has_cookie: bool
    masked_cookie: str = ""


# ---------------------------------------------------------------------------
# Trend → POD
# Các model *LLM* không có giá trị mặc định để tương thích Structured Outputs (strict).
# ---------------------------------------------------------------------------

TrendType = Literal[
    "event", "sports", "movie_tv", "music", "gaming", "meme",
    "seasonal", "social", "product", "news", "other",
]


class LLMTrend(BaseModel):
    name: str = Field(description="Tên trend ngắn gọn, tiếng Việt")
    keyword_en: str = Field(description="Từ khóa trend bằng tiếng Anh (như người Mỹ gọi)")
    trend_type: TrendType
    summary: str = Field(description="1-2 câu tiếng Việt: chuyện gì đang diễn ra, vì sao người Mỹ quan tâm")
    post_ids: List[str] = Field(description="post_id của các bài thuộc trend này (chỉ lấy từ dữ liệu đầu vào)")
    is_pod_friendly: bool = Field(description="Có phù hợp làm sản phẩm in ấn POD không")
    pod_reason: str = Field(description="Lý do ngắn (tiếng Việt) vì sao phù hợp / không phù hợp")


class LLMTrendList(BaseModel):
    trends: List[LLMTrend]


class DesignConcept(BaseModel):
    concept_name: str = Field(description="Tên concept, tiếng Việt")
    product_types: List[str] = Field(description="VD: t-shirt, hoodie, mug, sticker, poster, phone case, tote bag")
    text_on_design: str = Field(description="Chữ/slogan in trên sản phẩm, tiếng Anh giọng Mỹ; chuỗi rỗng nếu không có chữ")
    visual_description: str = Field(description="Mô tả hình ảnh, bố cục, tiếng Việt")
    style: str = Field(description="Phong cách: retro, vintage distressed, minimal line art, cartoon, typography...")
    color_palette: List[str] = Field(description="Bảng màu gợi ý (tên màu hoặc mã hex)")
    designer_prompt: str = Field(description="Prompt tiếng Anh chi tiết để designer/AI image tool tạo thiết kế in ấn")
    target_keywords: List[str] = Field(description="Từ khóa SEO tiếng Anh cho listing Etsy/Amazon")


class IpRisk(BaseModel):
    level: Literal["low", "medium", "high"]
    explanation: str = Field(description="Giải thích rủi ro bản quyền/thương hiệu, tiếng Việt")
    avoid: List[str] = Field(description="Từ ngữ, logo, nhân vật, tên người... tuyệt đối không dùng")
    safe_alternatives: List[str] = Field(description="Cách thể hiện thay thế an toàn")


class PodIdeas(BaseModel):
    audience: str = Field(description="Chân dung khách hàng mục tiêu tại Mỹ, tiếng Việt")
    peak_window: str = Field(description="Thời điểm/độ khẩn cấp nên lên sản phẩm, tiếng Việt")
    best_products: List[str]
    design_concepts: List[DesignConcept]
    ip_risk: IpRisk


class TrendItem(BaseModel):
    """Trend đã lưu (LLM output + điểm số tính bằng code + ý tưởng POD nếu đã tạo)."""
    trend_id: str
    name: str
    keyword_en: str
    trend_type: str
    summary: str
    is_pod_friendly: bool
    pod_reason: str
    post_ids: List[str]
    posts: List[Dict[str, Any]] = Field(default_factory=list)
    subreddits: List[str] = Field(default_factory=list)
    post_count: int = 0
    total_velocity: float = 0.0
    trend_score: float = 0.0
    detected_at: str = ""
    first_seen: str = ""          # Lần đầu phát hiện trend
    last_seen: str = ""           # Lần gần nhất trend xuất hiện lại
    prev_score: Optional[float] = None  # Điểm ở lần thấy trước đó (để biết đang lên/xuống)
    ideas: Optional[PodIdeas] = None
    ideas_generated_at: Optional[str] = None


class StatsOverview(BaseModel):
    total_posts: int = 0
    max_velocity: float = 0.0
    top_subreddit: str = "N/A"
    total_upvotes: int = 0
    total_comments: int = 0
    avg_velocity: float = 0.0
