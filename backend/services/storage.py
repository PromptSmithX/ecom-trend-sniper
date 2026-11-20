# -*- coding: utf-8 -*-
"""
backend/services/storage.py
---------------------------
Dịch vụ quản lý đọc/ghi dữ liệu bài viết (test_output.json)
và cài đặt phiên đăng nhập/danh sách subreddit (backend_settings.json).
"""

import json
from typing import List, Dict, Any, Optional
from backend.config import STORAGE_FILE, SETTINGS_FILE, DEFAULT_SUBREDDITS
from backend.schemas import StatsOverview


class StorageService:
    @staticmethod
    def load_posts() -> List[Dict[str, Any]]:
        """Đọc danh sách bài viết từ file test_output.json."""
        if not STORAGE_FILE.exists():
            return []
        try:
            with open(STORAGE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception:
            return []

    @staticmethod
    def save_posts(posts: List[Dict[str, Any]]) -> None:
        """Ghi danh sách bài viết vào file test_output.json."""
        with open(STORAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)

    @staticmethod
    def load_settings() -> Dict[str, Any]:
        """Đọc cài đặt cá nhân: cookie reddit_session, danh sách subreddits tùy chỉnh."""
        default_settings = {
            "reddit_session": "",
            "subreddits": DEFAULT_SUBREDDITS,
        }
        if not SETTINGS_FILE.exists():
            return default_settings
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                return {**default_settings, **loaded}
        except Exception:
            return default_settings

    @staticmethod
    def save_settings(settings: Dict[str, Any]) -> None:
        """Ghi cài đặt vào backend_settings.json."""
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)

    @classmethod
    def get_stats(cls) -> StatsOverview:
        """Tính toán các chỉ số thống kê từ tập dữ liệu hiện có."""
        posts = cls.load_posts()
        if not posts:
            return StatsOverview()

        total_posts = len(posts)
        max_vel = max((p.get("velocity_score", 0.0) for p in posts), default=0.0)
        total_up = sum(p.get("score", 0) for p in posts)
        total_comm = sum(p.get("comments", 0) for p in posts)
        avg_vel = sum(p.get("velocity_score", 0.0) for p in posts) / total_posts

        # Tìm subreddit có nhiều bài hoặc nhiều tương tác nhất
        sub_counts: Dict[str, int] = {}
        for p in posts:
            sub = p.get("subreddit", "Unknown")
            sub_counts[sub] = sub_counts.get(sub, 0) + 1
        top_sub = max(sub_counts.items(), key=lambda x: x[1])[0] if sub_counts else "N/A"

        return StatsOverview(
            total_posts=total_posts,
            max_velocity=round(max_vel, 2),
            top_subreddit=top_sub,
            total_upvotes=total_up,
            total_comments=total_comm,
            avg_velocity=round(avg_vel, 2),
        )

    @classmethod
    def filter_and_sort_posts(
        cls,
        search: Optional[str] = None,
        subreddit: Optional[str] = None,
        sort_by: str = "velocity_score",
        sort_order: str = "desc",
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Lọc và sắp xếp bài viết theo yêu cầu từ frontend."""
        posts = cls.load_posts()

        if search:
            query = search.lower().strip()
            posts = [p for p in posts if query in p.get("title", "").lower() or query in p.get("subreddit", "").lower()]

        if subreddit and subreddit.lower() != "all":
            posts = [p for p in posts if p.get("subreddit", "").lower() == subreddit.lower()]

        reverse = (sort_order.lower() == "desc")
        
        def sort_key(item: Dict[str, Any]):
            val = item.get(sort_by, 0)
            if val is None:
                return 0
            return val

        posts.sort(key=sort_key, reverse=reverse)
        return posts[:limit]
