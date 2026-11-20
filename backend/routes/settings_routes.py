# -*- coding: utf-8 -*-
"""
backend/routes/settings_routes.py
---------------------------------
Định tuyến API quản lý Cookie Reddit và danh sách Subreddit ưa thích.
"""

from fastapi import APIRouter
from typing import List
from backend.schemas import CookiePayload, CookieStatus
from backend.services.storage import StorageService
from backend.config import FEED_CATEGORIES

router = APIRouter(prefix="/api/settings", tags=["Settings"])


@router.get("")
def get_current_settings():
    """Lấy cài đặt người dùng hiện tại (danh sách subreddits, trạng thái cookie)."""
    settings = StorageService.load_settings()
    raw_cookie = settings.get("reddit_session", "")
    has_cookie = bool(raw_cookie and len(raw_cookie.strip()) > 5)
    
    masked = ""
    if has_cookie:
        masked = f"{raw_cookie[:6]}...{raw_cookie[-4:]}" if len(raw_cookie) > 10 else "******"

    return {
        "subreddits": settings.get("subreddits", []),
        "has_cookie": has_cookie,
        "masked_cookie": masked,
        "categories": FEED_CATEGORIES,
    }


@router.post("/cookie", response_model=CookieStatus)
def update_reddit_cookie(payload: CookiePayload):
    """Cập nhật giá trị cookie reddit_session."""
    settings = StorageService.load_settings()
    cookie_val = payload.reddit_session.strip()
    settings["reddit_session"] = cookie_val
    StorageService.save_settings(settings)

    has_cookie = bool(cookie_val)
    masked = f"{cookie_val[:6]}...{cookie_val[-4:]}" if len(cookie_val) > 10 else "******"
    return CookieStatus(has_cookie=has_cookie, masked_cookie=masked)


@router.delete("/cookie")
def delete_reddit_cookie():
    """Xóa cookie reddit_session đã lưu."""
    settings = StorageService.load_settings()
    settings["reddit_session"] = ""
    StorageService.save_settings(settings)
    return {"message": "Đã xóa cookie thành công."}


@router.post("/subreddits")
def update_subreddits(subreddits: List[str]):
    """Cập nhật danh sách subreddits theo dõi mặc định."""
    cleaned = [s.strip().replace("r/", "") for s in subreddits if s.strip()]
    settings = StorageService.load_settings()
    settings["subreddits"] = cleaned
    StorageService.save_settings(settings)
    return {"subreddits": cleaned}
