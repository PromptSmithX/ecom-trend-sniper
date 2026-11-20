# -*- coding: utf-8 -*-
"""
backend/services/scraper_engine.py
----------------------------------
Động cơ cào dữ liệu Reddit bất đồng bộ sử dụng curl_cffi (impersonate="chrome120").
Quản lý trạng thái cào, ghi log trực tiếp theo thời gian thực để hiển thị trên UI React.
"""

import time
import random
import threading
from datetime import datetime
from typing import List, Optional, Dict, Any

from curl_cffi import requests
from backend.config import BROWSER_HEADERS, FEED_CATEGORIES
from backend.services.dom_parser import parse_old_reddit_dom
from backend.services.storage import StorageService
from backend.schemas import ScrapeProgress, LogMessage


class ScraperEngine:
    def __init__(self):
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        
        self.progress = ScrapeProgress(
            is_running=False,
            current_step="Sẵn sàng",
            logs=[]
        )

    def get_progress(self) -> ScrapeProgress:
        with self._lock:
            return self.progress.model_copy()

    def add_log(self, level: str, message: str):
        now_str = datetime.now().strftime("%H:%M:%S")
        with self._lock:
            log_item = LogMessage(timestamp=now_str, level=level, message=message)
            self.progress.logs.append(log_item)
            # Giữ tối đa 200 logs gần nhất để tối ưu bộ nhớ
            if len(self.progress.logs) > 200:
                self.progress.logs.pop(0)

    def cancel(self):
        """Dừng tiến trình cào."""
        with self._lock:
            if self.progress.is_running:
                self._stop_event.set()
                self.add_log("warning", "Yêu cầu dừng tiến trình từ người dùng...")

    def start_scrape(
        self,
        subreddits: List[str],
        category_ids: List[str],
        delay_min: float = 2.0,
        delay_max: float = 4.0,
        cookie: Optional[str] = None
    ) -> bool:
        """Khởi động tác vụ cào trong luồng nền."""
        with self._lock:
            if self.progress.is_running:
                return False

            self._stop_event.clear()
            self.progress.is_running = True
            self.progress.completed_requests = 0
            self.progress.scraped_count = 0
            self.progress.logs = []
            
            # Tính tổng số request
            active_cats = [c for c in FEED_CATEGORIES if c["id"] in category_ids]
            if not active_cats:
                active_cats = FEED_CATEGORIES
            self.progress.total_requests = len(subreddits) * len(active_cats)

        self._thread = threading.Thread(
            target=self._run_worker,
            args=(subreddits, active_cats, delay_min, delay_max, cookie),
            daemon=True
        )
        self._thread.start()
        return True

    def _run_worker(
        self,
        subreddits: List[str],
        categories: List[Dict[str, Any]],
        delay_min: float,
        delay_max: float,
        cookie: Optional[str]
    ):
        self.add_log("info", f"Bắt đầu phiên cào: {len(subreddits)} Subreddits, {len(categories)} Danh mục")
        
        # Lấy cookie lưu trữ nếu không truyền trực tiếp
        if not cookie:
            settings = StorageService.load_settings()
            cookie = settings.get("reddit_session", "")

        session = requests.Session(impersonate="chrome120")
        if cookie:
            session.cookies.set("reddit_session", cookie, domain=".reddit.com")
            masked = f"{cookie[:6]}...{cookie[-4:]}" if len(cookie) > 10 else "***"
            self.add_log("success", f"Đã áp dụng cookie phiên reddit_session ({masked})")
        else:
            self.add_log("warning", "Chưa có cookie reddit_session (Nếu bị chặn chuyển hướng login, hãy cấu hình cookie)")

        # Đọc dữ liệu cũ để gộp bài mới
        existing_posts = StorageService.load_posts()
        seen_ids = {p["post_id"] for p in existing_posts}
        all_posts = list(existing_posts)
        newly_scraped = 0

        try:
            for sub_idx, sub in enumerate(subreddits, 1):
                if self._stop_event.is_set():
                    break

                with self._lock:
                    self.progress.current_subreddit = sub

                for cat in categories:
                    if self._stop_event.is_set():
                        break

                    cat_id = cat["id"]
                    cat_name = cat["name"]
                    cat_path = cat["path"]
                    url = f"https://old.reddit.com/r/{sub}/{cat_path}"

                    with self._lock:
                        self.progress.current_category = cat_name
                        self.progress.current_step = f"Đang quét r/{sub} [{cat_name}]"

                    self.add_log("info", f"Gửi GET -> {url}")

                    try:
                        resp = session.get(
                            url,
                            headers=BROWSER_HEADERS,
                            allow_redirects=False,
                            timeout=15
                        )
                        status = resp.status_code

                        if status == 200:
                            posts = parse_old_reddit_dom(resp.text, sub, cat_id)
                            added_here = 0
                            for p in posts:
                                pid = p["post_id"]
                                if pid not in seen_ids:
                                    seen_ids.add(pid)
                                    all_posts.append(p)
                                    newly_scraped += 1
                                    added_here += 1
                                else:
                                    # Cập nhật thông số mới nhất của bài viết
                                    for idx, op in enumerate(all_posts):
                                        if op["post_id"] == pid:
                                            all_posts[idx] = p
                                            break

                            self.add_log("success", f"✅ r/{sub} [{cat_name}]: Thu thập {len(posts)} bài (+{added_here} bài mới)")

                        elif status in (301, 302, 307, 308):
                            loc = resp.headers.get("Location", "")
                            if "login" in loc or "reason=lor2" in loc:
                                self.add_log("warning", f"🛡️ HTTP {status}: Reddit kích hoạt Login Wall (reason=lor2). Cần gắn cookie!")
                            else:
                                self.add_log("warning", f"HTTP {status} Chuyển hướng tới: {loc}")

                        elif status == 404:
                            self.add_log("error", f"❌ HTTP 404 Not Found: Subreddit 'r/{sub}' không tồn tại hoặc đã bị khóa.")

                        elif status == 403:
                            self.add_log("error", f"❌ HTTP 403 Forbidden: Bị từ chối quyền truy cập.")

                        elif status == 429:
                            self.add_log("error", f"❌ HTTP 429 Rate Limit: Quá giới hạn tần suất yêu cầu.")

                        else:
                            self.add_log("warning", f"HTTP {status}: Phản hồi lạ từ máy chủ Reddit.")

                    except Exception as e:
                        self.add_log("error", f"Lỗi mạng khi kết nối r/{sub}: {str(e)}")

                    with self._lock:
                        self.progress.completed_requests += 1
                        self.progress.scraped_count = newly_scraped

                    # Lưu dữ liệu sau mỗi request
                    StorageService.save_posts(all_posts)

                    # Nghỉ ngẫu nhiên giữa các request
                    if not self._stop_event.is_set():
                        sleep_s = round(random.uniform(delay_min, delay_max), 2)
                        self.add_log("info", f"⏳ Nghỉ ngơi an toàn {sleep_s}s...")
                        time.sleep(sleep_s)

        finally:
            with self._lock:
                self.progress.is_running = False
                self.progress.current_step = "Đã hoàn thành" if not self._stop_event.is_set() else "Đã dừng bởi người dùng"
            
            self.add_log("success", f"Hoàn tất phiên cào! Tổng bài trong cơ sở dữ liệu: {len(all_posts)} (+{newly_scraped} bài mới)")


# Singleton instance để chia sẻ trạng thái qua API
scraper_engine = ScraperEngine()
