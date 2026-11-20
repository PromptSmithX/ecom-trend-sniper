# -*- coding: utf-8 -*-
"""
backend/routes/trend_routes.py
------------------------------
API phát hiện trend và sinh ý tưởng sản phẩm POD bằng OpenAI.
"""

import os
from fastapi import APIRouter, HTTPException, Response

from backend.config import OPENAI_MODEL
from backend.services import trend_analyzer
from backend.services.trend_analyzer import TrendAnalyzerError

router = APIRouter(prefix="/api/trends", tags=["Trends"])


@router.get("")
def list_trends():
    """Danh sách trend đã phát hiện (kèm ý tưởng POD nếu đã tạo)."""
    return {
        "trends": trend_analyzer.load_trends(),
        "llm_configured": bool(os.getenv("OPENAI_API_KEY", "").strip()),
        "model": OPENAI_MODEL,
    }


@router.post("/detect")
def detect_trends():
    """Gom các bài đã cào thành trend bằng LLM."""
    try:
        return {"trends": trend_analyzer.detect_trends()}
    except TrendAnalyzerError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{trend_id}/ideas")
def generate_ideas(trend_id: str):
    """Sinh ý tưởng thiết kế POD + prompt cho designer cho 1 trend."""
    try:
        return trend_analyzer.generate_pod_ideas(trend_id)
    except TrendAnalyzerError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/export")
def export_ideas():
    """Xuất toàn bộ ý tưởng POD ra CSV để gửi designer."""
    return Response(
        content=trend_analyzer.export_ideas_csv(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=pod_ideas.csv"},
    )
