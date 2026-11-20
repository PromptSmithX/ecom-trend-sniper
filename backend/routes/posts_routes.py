# -*- coding: utf-8 -*-
"""
backend/routes/posts_routes.py
------------------------------
Định tuyến API truy vấn, thống kê và xuất dữ liệu bài viết.
"""

from fastapi import APIRouter, Query, Response
from typing import List, Optional
import json

from backend.schemas import PostItem, StatsOverview
from backend.services.storage import StorageService

router = APIRouter(prefix="/api/posts", tags=["Posts"])


@router.get("", response_model=List[PostItem])
def get_posts(
    search: Optional[str] = Query(None, description="Tìm kiếm theo tiêu đề hoặc subreddit"),
    subreddit: Optional[str] = Query(None, description="Lọc theo subreddit"),
    sort_by: str = Query("velocity_score", description="Trường cần sắp xếp"),
    sort_order: str = Query("desc", description="Thứ tự desc hoặc asc"),
    limit: int = Query(150, ge=1, le=500, description="Số lượng bài tối đa trả về"),
):
    """Truy vấn danh sách bài viết kèm tìm kiếm, lọc và sắp xếp."""
    return StorageService.filter_and_sort_posts(
        search=search,
        subreddit=subreddit,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
    )


@router.get("/stats", response_model=StatsOverview)
def get_posts_statistics():
    """Lấy các chỉ số thống kê tổng hợp (tổng bài, max velocity, top sub, ...)."""
    return StorageService.get_stats()


@router.delete("/clear")
def clear_all_posts():
    """Xóa sạch cơ sở dữ liệu hiện tại để làm mới."""
    StorageService.save_posts([])
    return {"message": "Đã làm trống cơ sở dữ liệu bài viết."}


@router.get("/export")
def export_posts_json():
    """Xuất file test_output.json trực tiếp từ trình duyệt."""
    posts = StorageService.load_posts()
    content = json.dumps(posts, ensure_ascii=False, indent=2)
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=test_output.json"},
    )
