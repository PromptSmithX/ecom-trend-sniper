# -*- coding: utf-8 -*-
"""
backend/routes/scrape_routes.py
-------------------------------
Định tuyến API điều khiển tiến trình cào dữ liệu: Bắt đầu, Xem trạng thái, Hủy bỏ.
"""

from fastapi import APIRouter, HTTPException
from backend.schemas import ScrapeRequest, ScrapeProgress
from backend.services.scraper_engine import scraper_engine

router = APIRouter(prefix="/api/scrape", tags=["Scrape"])


@router.post("/start")
def start_scrape_job(payload: ScrapeRequest):
    """Bắt đầu một phiên cào dữ liệu mới."""
    if not payload.subreddits:
        raise HTTPException(status_code=400, detail="Vui lòng cung cấp ít nhất một subreddit.")

    success = scraper_engine.start_scrape(
        subreddits=payload.subreddits,
        category_ids=payload.categories,
        delay_min=payload.delay_min,
        delay_max=payload.delay_max,
        cookie=payload.cookie
    )

    if not success:
        raise HTTPException(status_code=409, detail="Một tác vụ cào dữ liệu đang chạy. Vui lòng đợi hoặc bấm Hủy.")

    return {"message": "Đã bắt đầu tác vụ cào dữ liệu thành công."}


@router.get("/status", response_model=ScrapeProgress)
def get_scrape_status():
    """Lấy trạng thái và log thời gian thực của tác vụ cào."""
    return scraper_engine.get_progress()


@router.post("/cancel")
def cancel_scrape_job():
    """Hủy tiến trình cào đang thực hiện."""
    scraper_engine.cancel()
    return {"message": "Đã gửi tín hiệu dừng tiến trình."}
