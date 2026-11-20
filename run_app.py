#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_app.py
----------
Script khởi chạy duy nhất để khởi động toàn bộ hệ thống Reddit Trend Radar:
- Backend FastAPI (chạy tại http://127.0.0.1:8000)
- Tích hợp phục vụ trực tiếp Frontend React (đã build sẵn tại frontend/dist)
- Tự động mở trình duyệt web tới dashboard.
"""

import sys
import webbrowser
from pathlib import Path

# Thêm thư mục gốc vào sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

try:
    import uvicorn
    import fastapi
    from curl_cffi import requests
    from bs4 import BeautifulSoup
except ImportError as e:
    print(f"❌ Thiếu thư viện: {e}")
    print("👉 Hãy cài đặt: pip install -r requirements.txt")
    sys.exit(1)


def main():
    port = 8000
    host = "127.0.0.1"
    url = f"http://{host}:{port}"

    print("=" * 75)
    print("🚀 ĐANG KHỞI CHẠY REDDIT TREND VELOCITY RADAR")
    print("=" * 75)
    print(f"📡 Backend & Frontend UI : {url}")
    print(f"📖 Swagger API Docs       : {url}/docs")
    print(f"📂 Dữ liệu lưu trữ tại    : {BASE_DIR / 'test_output.json'}")
    print("=" * 75)
    print("💡 Mẹo: Bấm Ctrl + C trong terminal này để dừng dịch vụ khi không dùng.")
    print("-" * 75)

    # Mở trình duyệt web tự động
    try:
        webbrowser.open(url)
    except Exception:
        pass

    # Chạy máy chủ Uvicorn
    uvicorn.run("backend.main:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
