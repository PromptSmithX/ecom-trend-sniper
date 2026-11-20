# -*- coding: utf-8 -*-
"""
backend/main.py
---------------
Điểm khởi chạy ứng dụng FastAPI, tích hợp định tuyến, CORS
và hỗ trợ phục vụ trực tiếp bản build của React frontend.
"""

import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.routes.scrape_routes import router as scrape_router
from backend.routes.posts_routes import router as posts_router
from backend.routes.settings_routes import router as settings_router
from backend.routes.trend_routes import router as trend_router


class _SkipPollingAccessLog(logging.Filter):
    """Ẩn access log của endpoint polling trạng thái cào để terminal không bị spam."""

    def filter(self, record: logging.LogRecord) -> bool:
        return "/api/scrape/status" not in record.getMessage()


logging.getLogger("uvicorn.access").addFilter(_SkipPollingAccessLog())

app = FastAPI(
    title="Reddit Trend Velocity Radar API",
    description="Backend API phục vụ cào dữ liệu xu hướng Reddit sử dụng curl_cffi và BeautifulSoup",
    version="2.0.0"
)

# Cấu hình CORS để frontend React giao tiếp thuận tiện
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gắn các router API
app.include_router(scrape_router)
app.include_router(posts_router)
app.include_router(settings_router)
app.include_router(trend_router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "reddit-trend-radar-backend"}


# Phục vụ file tĩnh của frontend dist nếu đã build
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = FRONTEND_DIST / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
