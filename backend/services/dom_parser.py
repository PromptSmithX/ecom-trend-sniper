# -*- coding: utf-8 -*-
"""
backend/services/dom_parser.py
------------------------------
Module bóc tách cấu trúc HTML từ old.reddit.com bằng BeautifulSoup (lxml).
Đảm bảo liên kết bài viết được chuẩn hóa theo Cách 1: dùng https://old.reddit.com
để tránh bị DNS sinkhole chặn ở Việt Nam.
"""

import re
import time
from datetime import datetime
from typing import List, Dict, Any
from bs4 import BeautifulSoup


def parse_old_reddit_dom(html_content: str, subreddit: str, category: str) -> List[Dict[str, Any]]:
    """
    Bóc tách các thẻ div.thing trên old.reddit.com:
    - Loại bỏ thẻ promoted / quảng cáo
    - Trích xuất: post_id, title, url (old.reddit), standard_url (www.reddit), score, comments, created_utc
    - Tính velocity_score = (score + comments * 2) / hours_since_posted (min 0.5h)
    """
    soup = BeautifulSoup(html_content, "lxml")
    things = soup.find_all("div", class_="thing")
    
    extracted: List[Dict[str, Any]] = []
    current_epoch = time.time()

    for thing in things:
        classes = thing.get("class", [])
        if "promoted" in classes or "promotedlink" in classes:
            continue

        # post_id: từ data-fullname (vd: t3_1h2345)
        post_id = thing.get("data-fullname") or thing.get("id") or ""
        if not post_id:
            continue

        # title: a.title
        title_elem = thing.find("a", class_="title")
        title = title_elem.get_text(strip=True) if title_elem else ""

        # permalink
        permalink = thing.get("data-permalink") or ""
        if not permalink and title_elem and title_elem.get("href"):
            permalink = title_elem["href"]

        # Chuẩn hóa link:
        # Cách 1: Sử dụng old.reddit.com để người dùng Việt Nam mở được trực tiếp
        if permalink.startswith("http"):
            url_old = permalink.replace("https://www.reddit.com", "https://old.reddit.com")
            url_standard = permalink.replace("https://old.reddit.com", "https://www.reddit.com")
        else:
            clean_perm = "/" + permalink.lstrip("/")
            url_old = f"https://old.reddit.com{clean_perm}"
            url_standard = f"https://www.reddit.com{clean_perm}"

        # score: lấy từ title của div.score.unvoted
        score = 0
        score_elem = thing.find("div", class_=lambda c: c and "score" in c.split() and "unvoted" in c.split())
        if score_elem and score_elem.get("title"):
            try:
                score = int(score_elem["title"])
            except ValueError:
                score = 0
        elif score_elem and score_elem.get_text(strip=True).isdigit():
            score = int(score_elem.get_text(strip=True))
        elif thing.get("data-score"):
            try:
                score = int(thing["data-score"])
            except ValueError:
                score = 0

        # comments: số đầu tiên trong a.comments
        comments = 0
        comments_elem = thing.find("a", class_="comments")
        if comments_elem:
            match = re.search(r"(\d+)", comments_elem.get_text())
            if match:
                comments = int(match.group(1))

        # created_utc: từ data-timestamp (chia 1000)
        created_utc = 0.0
        raw_ts = thing.get("data-timestamp")
        if raw_ts:
            try:
                created_utc = float(raw_ts) / 1000.0
            except (ValueError, TypeError):
                created_utc = 0.0
        else:
            time_elem = thing.find("time")
            if time_elem and time_elem.get("datetime"):
                try:
                    dt = datetime.fromisoformat(time_elem["datetime"].replace("Z", "+00:00"))
                    created_utc = dt.timestamp()
                except Exception:
                    created_utc = 0.0

        # Tính velocity_score
        if created_utc > 0:
            hours_since_posted = (current_epoch - created_utc) / 3600.0
        else:
            hours_since_posted = 1.0

        hours_since_posted = max(hours_since_posted, 0.5)
        velocity_score = round((score + (comments * 2)) / hours_since_posted, 2)

        extracted.append({
            "post_id": post_id,
            "subreddit": subreddit,
            "category": category,
            "title": title,
            "url": url_old,
            "standard_url": url_standard,
            "score": score,
            "comments": comments,
            "created_utc": round(created_utc, 2),
            "hours_since_posted": round(hours_since_posted, 2),
            "velocity_score": velocity_score,
        })

    return extracted
