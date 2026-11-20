# -*- coding: utf-8 -*-
"""
backend/services/trend_analyzer.py
----------------------------------
Phân tích trend bằng OpenAI cho mục đích sản phẩm POD (thị trường Mỹ):
1. detect_trends(): gom các bài Reddit đang hot thành "trend" (LLM), chấm điểm bằng code.
2. generate_pod_ideas(): với 1 trend, sinh concept thiết kế + prompt cho designer + cảnh báo IP.

API key chỉ đọc từ biến môi trường OPENAI_API_KEY.
"""

import csv
import io
import json
import os
import re
import hashlib
import threading
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Type, TypeVar

from pydantic import BaseModel

from backend.config import (
    OPENAI_MODEL,
    TRENDS_FILE,
    TREND_LOOKBACK_HOURS,
    TREND_MAX_POSTS,
    TREND_RETENTION_DAYS,
)
from backend.schemas import LLMTrendList, PodIdeas, TrendItem
from backend.services.storage import StorageService

T = TypeVar("T", bound=BaseModel)

_file_lock = threading.Lock()


class TrendAnalyzerError(Exception):
    """Lỗi có thông báo thân thiện để trả về frontend."""


# ---------------------------------------------------------------------------
# OpenAI helper
# ---------------------------------------------------------------------------

def _call_llm(system: str, user: str, response_format: Type[T]) -> T:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise TrendAnalyzerError(
            "Chưa cấu hình OPENAI_API_KEY. Hãy thêm vào file .env ở thư mục dự án "
            "(OPENAI_API_KEY=sk-...) rồi khởi động lại ứng dụng."
        )

    try:
        from openai import OpenAI
    except ImportError as e:
        raise TrendAnalyzerError("Thiếu thư viện openai. Chạy: pip install -r requirements.txt") from e

    client = OpenAI(api_key=api_key, timeout=180)
    try:
        completion = client.chat.completions.parse(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format=response_format,
        )
    except Exception as e:  # lỗi mạng, sai key, model không tồn tại...
        raise TrendAnalyzerError(f"Lỗi gọi OpenAI ({OPENAI_MODEL}): {e}") from e

    message = completion.choices[0].message
    if getattr(message, "refusal", None):
        raise TrendAnalyzerError(f"Model từ chối yêu cầu: {message.refusal}")
    if message.parsed is None:
        raise TrendAnalyzerError("Model không trả về dữ liệu hợp lệ, hãy thử lại.")
    return message.parsed


# ---------------------------------------------------------------------------
# Lưu trữ trends.json
# ---------------------------------------------------------------------------

def load_trends() -> List[Dict[str, Any]]:
    with _file_lock:
        if not TRENDS_FILE.exists():
            return []
        try:
            with open(TRENDS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except Exception:
            return []


def _save_trends(trends: List[Dict[str, Any]]) -> None:
    with _file_lock:
        with open(TRENDS_FILE, "w", encoding="utf-8") as f:
            json.dump(trends, f, ensure_ascii=False, indent=2)


def _make_trend_id(keyword_en: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", keyword_en.lower()).strip("-")[:40] or "trend"
    digest = hashlib.md5(keyword_en.lower().strip().encode("utf-8")).hexdigest()[:6]
    return f"{slug}-{digest}"


# ---------------------------------------------------------------------------
# 1. Phát hiện trend
# ---------------------------------------------------------------------------

DETECT_SYSTEM = """Bạn là chuyên gia nghiên cứu xu hướng cho một công ty bán sản phẩm Print-on-Demand (áo thun, hoodie, cốc, sticker, poster, ốp điện thoại...) tại thị trường Mỹ.

Nhiệm vụ: đọc danh sách bài Reddit đang hot và gom chúng thành các TREND (chủ đề mà nhiều người Mỹ đang quan tâm/bàn tán).

Quy tắc:
- Mỗi trend là một chủ đề cụ thể (sự kiện, trận đấu/giải đấu, phim/series, bài hát/nghệ sĩ, game, meme, dịp lễ/mùa, phong trào xã hội...). Không tạo trend quá chung chung như "bóng đá" hay "phim ảnh".
- Một trend có thể chỉ gồm 1 bài nếu bài đó rất hot, nhưng ưu tiên chủ đề được nhắc ở nhiều bài/nhiều subreddit.
- post_ids CHỈ được lấy từ dữ liệu đầu vào. Không bịa post_id.
- Bỏ qua bài là câu hỏi cá nhân lặt vặt không thành chủ đề.
- is_pod_friendly = false với: thảm họa, chết chóc, tội phạm, bệnh tật, tranh cãi chính trị gây chia rẽ, tin tức khô khan không có yếu tố cảm xúc/bản sắc để người ta muốn mặc hoặc tặng.
- is_pod_friendly = true khi trend tạo ra niềm tự hào, sự hài hước, cảm giác thuộc về một cộng đồng fan, hoặc gắn với dịp tặng quà.
- Trả về tối đa 40 trend, sắp xếp từ nổi bật nhất. Viết name, summary, pod_reason bằng tiếng Việt; keyword_en bằng tiếng Anh.
- Nếu được cung cấp danh sách TREND ĐÃ CÓ: khi một trend mới cùng chủ đề với trend đã có, BẮT BUỘC dùng lại đúng y nguyên keyword_en của trend đã có (để hệ thống gộp lại, không tạo trùng)."""


def _select_recent_posts(
    posts: List[Dict[str, Any]], subreddits: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Bài trong TREND_LOOKBACK_HOURS, (tùy chọn) chỉ thuộc các subreddit đang chọn, top theo velocity."""
    now = time.time()
    cutoff = now - TREND_LOOKBACK_HOURS * 3600
    allowed = {s.lower() for s in subreddits} if subreddits else None
    recent = [
        p for p in posts
        if p.get("created_utc", 0) >= cutoff
        and p.get("title")
        and (allowed is None or p.get("subreddit", "").lower() in allowed)
    ]
    recent.sort(key=lambda p: p.get("velocity_score", 0.0), reverse=True)
    return recent[:TREND_MAX_POSTS]


def _post_summary(p: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "post_id": p["post_id"],
        "title": p["title"],
        "subreddit": p["subreddit"],
        "url": p["url"],
        "score": p.get("score", 0),
        "comments": p.get("comments", 0),
        "velocity_score": p.get("velocity_score", 0.0),
    }


def _parse_ts(value: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(value) if value else None
    except ValueError:
        return None


def _sort_trends(trends: List[Dict[str, Any]]) -> None:
    """Hợp POD trước → trend thấy ở lần phát hiện gần nhất → điểm cao."""
    latest = max((t.get("last_seen", "") for t in trends), default="")
    trends.sort(key=lambda x: (
        not x.get("is_pod_friendly"),
        x.get("last_seen", "") != latest,
        -x.get("trend_score", 0.0),
    ))


def detect_trends() -> List[Dict[str, Any]]:
    current_subs = StorageService.load_settings().get("subreddits") or []
    posts = _select_recent_posts(StorageService.load_posts(), current_subs)
    if not posts:
        raise TrendAnalyzerError(
            f"Không có bài viết nào trong {TREND_LOOKBACK_HOURS}h gần đây thuộc các subreddit đang chọn. "
            "Hãy bấm \"Cào dữ liệu ngay\" trước khi phát hiện trend."
        )

    existing = load_trends()
    by_id = {p["post_id"]: p for p in posts}
    lines = [
        f"{p['post_id']} | r/{p['subreddit']} | {p.get('score', 0)} upvotes | "
        f"{p.get('comments', 0)} comments | {p['title']}"
        for p in posts
    ]
    known = "\n".join(f"- {t['keyword_en']} ({t['name']})" for t in existing[:80])
    today = datetime.now().strftime("%Y-%m-%d")
    user = (
        f"Hôm nay là {today}.\n\n"
        + (f"TREND ĐÃ CÓ (dùng lại đúng keyword_en nếu cùng chủ đề):\n{known}\n\n" if known else "")
        + f"Dưới đây là {len(posts)} bài Reddit hot nhất trong {TREND_LOOKBACK_HOURS}h qua.\n"
        "Định dạng: post_id | subreddit | upvotes | comments | title\n\n" + "\n".join(lines)
    )

    result = _call_llm(DETECT_SYSTEM, user, LLMTrendList)

    now = datetime.now()
    now_iso = now.isoformat(timespec="seconds")
    merged: Dict[str, Dict[str, Any]] = {t["trend_id"]: t for t in existing}

    seen_now = set()
    for t in result.trends:
        valid_ids = [pid for pid in dict.fromkeys(t.post_ids) if pid in by_id]
        if not valid_ids:
            continue  # LLM bịa post_id hoặc rỗng → bỏ
        trend_id = _make_trend_id(t.keyword_en)
        if trend_id in seen_now:
            continue
        seen_now.add(trend_id)

        # Số liệu của LẦN PHÁT HIỆN NÀY (để so sánh đang lên/xuống giữa các lần)
        trend_posts = [by_id[pid] for pid in valid_ids]
        subs = sorted({p["subreddit"] for p in trend_posts})
        total_vel = round(sum(p.get("velocity_score", 0.0) for p in trend_posts), 2)
        # Điểm trend tính bằng code: tổng velocity × số subreddit khác nhau cùng nhắc tới
        trend_score = round(total_vel * len(subs), 2)

        old = merged.get(trend_id)

        # Bài nguồn: gộp bài mới + bài cũ (bài mới có số liệu cập nhật hơn)
        sources = {p["post_id"]: p for p in (old or {}).get("posts", [])}
        sources.update({p["post_id"]: _post_summary(p) for p in trend_posts})
        all_posts = sorted(sources.values(), key=lambda x: x.get("velocity_score", 0.0), reverse=True)

        item = TrendItem(
            trend_id=trend_id,
            name=t.name,
            keyword_en=t.keyword_en,
            trend_type=t.trend_type,
            summary=t.summary,
            is_pod_friendly=t.is_pod_friendly,
            pod_reason=t.pod_reason,
            post_ids=[p["post_id"] for p in all_posts],
            posts=all_posts,
            subreddits=subs,
            post_count=len(trend_posts),
            total_velocity=total_vel,
            trend_score=trend_score,
            detected_at=now_iso,
            first_seen=(old or {}).get("first_seen") or (old or {}).get("detected_at") or now_iso,
            last_seen=now_iso,
            prev_score=(old or {}).get("trend_score") if old else None,
        ).model_dump()

        if old and old.get("ideas"):
            item["ideas"] = old["ideas"]
            item["ideas_generated_at"] = old.get("ideas_generated_at")
        merged[trend_id] = item

    # Bỏ trend lâu không xuất hiện lại
    cutoff = now - timedelta(days=TREND_RETENTION_DAYS)
    trends = []
    for t in merged.values():
        t.setdefault("first_seen", t.get("detected_at", ""))
        t.setdefault("last_seen", t.get("detected_at", ""))
        t.setdefault("prev_score", None)
        seen = _parse_ts(t["last_seen"])
        if seen is None or seen >= cutoff:
            trends.append(t)

    _sort_trends(trends)
    _save_trends(trends)
    return trends


# ---------------------------------------------------------------------------
# 2. Sinh ý tưởng POD cho 1 trend
# ---------------------------------------------------------------------------

IDEAS_SYSTEM = """Bạn là Creative Director của một thương hiệu Print-on-Demand bán tại Mỹ (Etsy, Amazon Merch, TikTok Shop, Shopify).

Nhiệm vụ: từ một trend đang hot, đề xuất hướng phát triển sản phẩm in ấn bán được cho khách hàng Mỹ.

Yêu cầu:
- 3 đến 5 design concept khác nhau về góc tiếp cận (hài hước, tự hào fan, tối giản, vintage/retro, quà tặng...).
- text_on_design: slogan tiếng Anh tự nhiên, ngắn, đúng văn hóa/tiếng lóng Mỹ, dễ đọc khi in.
- designer_prompt: prompt tiếng Anh chi tiết, đủ để designer hoặc công cụ AI tạo ảnh làm ngay: chủ thể, bố cục, phong cách, màu, typography, "isolated on transparent background, print-ready, high contrast, vector style" khi phù hợp, và nêu rõ những gì KHÔNG được đưa vào (logo, tên thương hiệu, người thật...).
- target_keywords: từ khóa SEO tiếng Anh người Mỹ hay tìm.
- BẢN QUYỀN & THƯƠNG HIỆU là ưu tiên số 1: KHÔNG dùng tên/logo/biểu tượng đã đăng ký (VD: FIFA, World Cup, NFL, Super Bowl, NBA, tên đội, Disney, Marvel, tên phim/game), KHÔNG dùng tên/hình người thật (cầu thủ, ca sĩ, diễn viên, chính trị gia), KHÔNG dùng nhân vật, câu thoại đặc trưng có bản quyền. Hãy thể hiện trend bằng biểu tượng chung, cảm xúc của fan, câu nói tự sáng tạo. Ghi rõ mọi thứ cần tránh vào ip_risk.avoid.
- peak_window: dựa trên ngày hiện tại, nói rõ nên lên sản phẩm khi nào và trend có thể kéo dài bao lâu.
- Phần mô tả/giải thích viết bằng tiếng Việt; slogan, prompt, keyword viết bằng tiếng Anh."""


def generate_pod_ideas(trend_id: str) -> Dict[str, Any]:
    trends = load_trends()
    trend = next((t for t in trends if t["trend_id"] == trend_id), None)
    if trend is None:
        raise TrendAnalyzerError("Không tìm thấy trend. Hãy chạy lại \"Phát hiện trend\".")

    titles = "\n".join(
        f"- r/{p['subreddit']} ({p['score']} upvotes, {p['comments']} comments): {p['title']}"
        for p in trend.get("posts", [])[:20]
    )
    today = datetime.now().strftime("%Y-%m-%d")
    user = (
        f"Hôm nay là {today}.\n"
        f"Trend: {trend['name']} ({trend['keyword_en']})\n"
        f"Loại: {trend['trend_type']}\n"
        f"Tóm tắt: {trend['summary']}\n"
        f"Subreddit đang bàn tán: {', '.join('r/' + s for s in trend['subreddits'])}\n"
        f"Các bài Reddit liên quan:\n{titles}"
    )

    ideas = _call_llm(IDEAS_SYSTEM, user, PodIdeas)

    trend["ideas"] = ideas.model_dump()
    trend["ideas_generated_at"] = datetime.now().isoformat(timespec="seconds")
    # Ghi lại (đọc mới nhất để không mất dữ liệu nếu có thay đổi song song)
    latest = load_trends()
    for idx, t in enumerate(latest):
        if t["trend_id"] == trend_id:
            latest[idx] = trend
            break
    else:
        latest.append(trend)
    _save_trends(latest)
    return trend


# ---------------------------------------------------------------------------
# 3. Xuất CSV cho designer
# ---------------------------------------------------------------------------

def export_ideas_csv() -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Trend", "Keyword (EN)", "Trend score", "Peak window", "Concept", "Products",
        "Text on design", "Visual", "Style", "Colors", "Designer prompt",
        "SEO keywords", "IP risk", "Avoid", "Reddit sources",
    ])
    for t in load_trends():
        ideas: Optional[Dict[str, Any]] = t.get("ideas")
        if not ideas:
            continue
        risk = ideas.get("ip_risk", {})
        sources = " | ".join(p["url"] for p in t.get("posts", [])[:5])
        for c in ideas.get("design_concepts", []):
            writer.writerow([
                t["name"], t["keyword_en"], t["trend_score"], ideas.get("peak_window", ""),
                c["concept_name"], ", ".join(c["product_types"]), c["text_on_design"],
                c["visual_description"], c["style"], ", ".join(c["color_palette"]),
                c["designer_prompt"], ", ".join(c["target_keywords"]),
                risk.get("level", ""), "; ".join(risk.get("avoid", [])), sources,
            ])
    # BOM để Excel đọc đúng tiếng Việt
    return "﻿" + output.getvalue()
