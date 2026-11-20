# -*- coding: utf-8 -*-
"""
backend/config.py
-----------------
Cấu hình tập trung cho ứng dụng Backend Reddit Scraper API.
"""

from pathlib import Path
import os

# Đường dẫn thư mục gốc dự án
BASE_DIR = Path(__file__).resolve().parent.parent


def _load_dotenv(path: Path) -> None:
    """Đọc file .env đơn giản (KEY=VALUE), không ghi đè biến môi trường đã có."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv(BASE_DIR / ".env")

# File lưu trữ dữ liệu cào được
STORAGE_FILE = BASE_DIR / "test_output.json"

# File cấu hình phiên đăng nhập & cài đặt người dùng
SETTINGS_FILE = BASE_DIR / "backend_settings.json"

# Preset săn trend đại chúng tại Mỹ cho sản phẩm POD (sự kiện, thể thao, phim, meme...)
TREND_SUBREDDITS = [
    "popular",
    "OutOfTheLoop",
    "soccer",
    "nfl",
    "nba",
    "movies",
    "television",
    "gaming",
    "Music",
    "memes",
    "popculturechat",
    # Thể thao
    "CFB",
    "baseball",
    "hockey",
    "formula1",
    "SquaredCircle",
    "MMA",
    # Giải trí
    "entertainment",
    "Fauxmoi",
    "anime",
    # Thể loại nhạc
    "popheads",
    "hiphopheads",
    "CountryMusic",
]

# Danh sách Subreddit mặc định = preset "Trend POD Mỹ"
DEFAULT_SUBREDDITS = list(TREND_SUBREDDITS)

# File lưu kết quả phân tích trend & ý tưởng POD
TRENDS_FILE = BASE_DIR / "trends.json"

# Cấu hình OpenAI (API key CHỈ đọc từ biến môi trường, không lưu file, không trả về frontend)
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")
TREND_LOOKBACK_HOURS = 48      # Chỉ phân tích bài đăng trong khoảng thời gian này
TREND_MAX_POSTS = 300          # Số bài (theo velocity) gửi cho LLM để gom trend
TREND_RETENTION_DAYS = 3       # Giữ trend không xuất hiện lại tối đa bao nhiêu ngày

# Các danh mục cào hỗ trợ
FEED_CATEGORIES = [
    {
        "id": "rising",
        "name": "Rising",
        "description": "Bắt trend mới nổi cực sớm",
        "path": "rising/",
    },
    {
        "id": "top_day",
        "name": "Top (24h)",
        "description": "Các bài hot nhất trong ngày",
        "path": "top/?sort=top&t=day",
    },
]

# User-Agent & Headers chuẩn Chrome 120
BROWSER_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
    "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}
