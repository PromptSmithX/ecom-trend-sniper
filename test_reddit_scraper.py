#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_reddit_scraper.py
----------------------
Script Python độc lập để kiểm tra khả năng cào dữ liệu bắt trend trên Reddit
sử dụng curl_cffi (impersonate="chrome120") và BeautifulSoup (parser lxml).

Yêu cầu kỹ thuật:
1. Thư viện: curl_cffi.requests (impersonate="chrome120") và BeautifulSoup (lxml).
2. Nguồn dữ liệu: https://old.reddit.com/r/{subreddit}/rising/ và top/?sort=top&t=day
3. Subreddit test: TikTokMadeMeBuyIt, BuyItForLife, gadgets.
4. Bóc tách DOM trên old.reddit.com (div.thing, a.title, div.score.unvoted, a.comments, data-timestamp).
5. Tính velocity_score = (score + comments * 2) / số_giờ_đã_đăng (tối thiểu 0.5 giờ).
6. Xuất terminal thống kê + Top 5 velocity và lưu test_output.json.
"""

import os
import re
import sys
import json
import time
import random
import argparse
from typing import List, Dict, Any, Optional

try:
    from curl_cffi import requests
except ImportError:
    print("❌ Lỗi: Thư viện 'curl_cffi' chưa được cài đặt.")
    print("👉 Hãy chạy: pip install curl_cffi")
    sys.exit(1)

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("❌ Lỗi: Thư viện 'beautifulsoup4' hoặc 'lxml' chưa được cài đặt.")
    print("👉 Hãy chạy: pip install beautifulsoup4 lxml")
    sys.exit(1)

# Danh sách subreddit cần cào
SUBREDDITS = ["TikTokMadeMeBuyIt", "BuyItForLife", "gadgets"]

# Các danh mục cần lấy dữ liệu
CATEGORIES = [
    {"name": "rising", "path": "rising/"},
    {"name": "top_day", "path": "top/?sort=top&t=day"},
]

# Headers giả lập Chrome thực tế
DEFAULT_HEADERS = {
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


def parse_old_reddit_dom(html_content: str, subreddit_name: str, category_name: str) -> List[Dict[str, Any]]:
    """
    Bóc tách DOM của old.reddit.com:
    - Tìm các thẻ div.thing (bỏ qua thẻ có class 'promoted').
    - Lấy: post_id, title, url, score, comments, created_utc.
    - Tính velocity_score = (score + comments * 2) / số_giờ_đã_đăng (min 0.5h).
    """
    soup = BeautifulSoup(html_content, "lxml")
    things = soup.find_all("div", class_="thing")
    
    extracted_posts = []
    current_timestamp = time.time()

    for thing in things:
        # 1. Bỏ qua thẻ có class 'promoted' hoặc 'promotedlink'
        classes = thing.get("class", [])
        if "promoted" in classes or "promotedlink" in classes:
            continue

        # 2. post_id: từ data-fullname (vd: t3_1h2345)
        post_id = thing.get("data-fullname") or thing.get("id") or ""
        if not post_id:
            continue

        # 3. title: a.title
        title_elem = thing.find("a", class_="title")
        title = title_elem.get_text(strip=True) if title_elem else ""

        # 4. url: data-permalink nối với https://www.reddit.com
        permalink = thing.get("data-permalink") or ""
        if permalink:
            if permalink.startswith("http"):
                post_url = permalink
            else:
                post_url = f"https://www.reddit.com{permalink}"
        elif title_elem and title_elem.get("href"):
            href = title_elem["href"]
            post_url = f"https://www.reddit.com{href}" if href.startswith("/") else href
        else:
            post_url = ""

        # 5. score: thuộc tính title của div.score.unvoted, nếu không có mặc định là 0
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

        # 6. comments: số đầu tiên trong text của a.comments
        comments = 0
        comments_elem = thing.find("a", class_="comments")
        if comments_elem:
            comments_text = comments_elem.get_text()
            match = re.search(r"(\d+)", comments_text)
            if match:
                comments = int(match.group(1))

        # 7. created_utc: từ data-timestamp chia 1000
        created_utc = 0.0
        raw_timestamp = thing.get("data-timestamp")
        if raw_timestamp:
            try:
                created_utc = float(raw_timestamp) / 1000.0
            except (ValueError, TypeError):
                created_utc = 0.0

        # 8. Tính chỉ số velocity_score = (score + comments * 2) / số_giờ_đã_đăng (tối thiểu 0.5h)
        if created_utc > 0:
            hours_since_posted = (current_timestamp - created_utc) / 3600.0
        else:
            hours_since_posted = 1.0  # Giá trị phòng ngừa nếu không có timestamp

        hours_since_posted = max(hours_since_posted, 0.5)
        velocity_score = round((score + (comments * 2)) / hours_since_posted, 2)

        extracted_posts.append({
            "post_id": post_id,
            "subreddit": subreddit_name,
            "category": category_name,
            "title": title,
            "url": post_url,
            "score": score,
            "comments": comments,
            "created_utc": round(created_utc, 2),
            "hours_since_posted": round(hours_since_posted, 2),
            "velocity_score": velocity_score,
        })

    return extracted_posts


def scrape_reddit(reddit_session_cookie: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Thực hiện cào dữ liệu từ 3 subreddit với curl_cffi (impersonate='chrome120').
    """
    session = requests.Session(impersonate="chrome120")
    
    # Thiết lập cookie nếu có (để vượt qua login wall reason=lor2 của old.reddit)
    if reddit_session_cookie:
        session.cookies.set("reddit_session", reddit_session_cookie, domain=".reddit.com")
        print(f"🔑 Đã kích hoạt cookie phiên Reddit: {reddit_session_cookie[:8]}... (ẩn)")

    all_scraped_posts: List[Dict[str, Any]] = []
    seen_post_ids = set()
    subreddit_stats: Dict[str, int] = {sub: 0 for sub in SUBREDDITS}
    blocked_requests = 0

    print("=" * 80)
    print("🚀 BẮT ĐẦU CÀO DỮ LIỆU REDDIT (curl_cffi chrome120 + BeautifulSoup lxml)")
    print(f"📌 Subreddits: {', '.join(SUBREDDITS)}")
    print("=" * 80)

    for sub_idx, sub in enumerate(SUBREDDITS, 1):
        print(f"\n📂 [{sub_idx}/{len(SUBREDDITS)}] Đang quét Subreddit: r/{sub}")

        for cat in CATEGORIES:
            cat_name = cat["name"]
            cat_path = cat["path"]
            target_url = f"https://old.reddit.com/r/{sub}/{cat_path}"

            print(f"   -> Gửi GET request tới: {target_url} ...")

            try:
                # Sử dụng allow_redirects=False để chủ động bắt mã HTTP 302/Login Wall
                response = session.get(
                    target_url,
                    headers=DEFAULT_HEADERS,
                    allow_redirects=False,
                    timeout=15
                )

                status_code = response.status_code

                # Xử lý các mã phản hồi bị chặn hoặc chuyển hướng đăng nhập
                if status_code in (301, 302, 307, 308):
                    location = response.headers.get("Location", "")
                    print(f"      ⚠️ [HTTP {status_code} Chuyển Hướng] URL đích: {location}")
                    if "login" in location or "reason=lor2" in location:
                        print("      🛡️ [BỊ CHẶN BỞI LOGIN WALL] Reddit kích hoạt cơ chế `reason=lor2` yêu cầu đăng nhập.")
                        print("         (Gợi ý: Cung cấp cookie 'reddit_session' bằng cách đặt biến môi trường REDDIT_SESSION hoặc qua tham số --cookie)")
                    blocked_requests += 1

                elif status_code == 403:
                    print(f"      ❌ [BỊ CHẶN HTTP 403 Forbidden] Reddit từ chối truy cập từ IP/Client này.")
                    blocked_requests += 1

                elif status_code == 429:
                    print(f"      ❌ [BỊ CHẶN HTTP 429 Too Many Requests] Đã chạm giới hạn Rate Limit của Reddit.")
                    blocked_requests += 1

                elif status_code == 200:
                    html_content = response.text
                    posts = parse_old_reddit_dom(html_content, sub, cat_name)
                    new_posts_count = 0

                    for p in posts:
                        pid = p["post_id"]
                        if pid not in seen_post_ids:
                            seen_post_ids.add(pid)
                            all_scraped_posts.append(p)
                            subreddit_stats[sub] += 1
                            new_posts_count += 1

                    print(f"      ✅ [HTTP 200 OK] Bóc tách thành công {len(posts)} bài (mới: {new_posts_count}).")

                else:
                    print(f"      ❓ [HTTP {status_code}] Phản hồi không mong muốn từ máy chủ.")

            except Exception as ex:
                print(f"      💥 [LỖI NGOẠI LỆ] {type(ex).__name__}: {ex}")

            # Nghỉ ngẫu nhiên 2 - 4 giây giữa các request theo đúng yêu cầu
            sleep_time = round(random.uniform(2.0, 4.0), 2)
            print(f"      ⏳ Nghỉ {sleep_time}s trước request kế tiếp...")
            time.sleep(sleep_time)

    # Hiển thị thống kê tổng kết
    print("\n" + "=" * 80)
    print("📊 THỐNG KÊ SỐ LƯỢNG BÀI CÀO ĐƯỢC:")
    print("=" * 80)
    for sub, count in subreddit_stats.items():
        print(f" • r/{sub:<20}: {count} bài")
    print(f" • Tổng số bài thu thập : {len(all_scraped_posts)} bài")
    if blocked_requests > 0:
        print(f" • Số request bị chặn/đăng nhập: {blocked_requests}/{len(SUBREDDITS) * len(CATEGORIES)}")

    # Lấy và hiển thị Top 5 bài có velocity_score cao nhất
    print("\n" + "=" * 80)
    print("🔥 TOP 5 BÀI VIẾT CÓ CHỈ SỐ VELOCITY_SCORE CAO NHẤT:")
    print("=" * 80)
    
    if all_scraped_posts:
        top_5_posts = sorted(all_scraped_posts, key=lambda x: x["velocity_score"], reverse=True)[:5]
        for rank, post in enumerate(top_5_posts, 1):
            print(f"\n#{rank} [Velocity Score: {post['velocity_score']}] - r/{post['subreddit']} ({post['category']})")
            print(f"   Tiêu đề : {post['title']}")
            print(f"   Điểm số : {post['score']} upvotes | Bình luận: {post['comments']} comments")
            print(f"   Đã đăng : {post['hours_since_posted']} giờ trước")
            print(f"   URL     : {post['url']}")
    else:
        print("⚠️ Chưa có bài viết nào được thu thập (có thể do Reddit yêu cầu đăng nhập đối với old.reddit.com).")
        print("💡 Xem mục hướng dẫn bên dưới để kích hoạt cookie hoặc chạy chế độ demo kiểm thử DOM.")

    # Lưu toàn bộ dữ liệu ra file test_output.json
    output_filename = "test_output.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(all_scraped_posts, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 80)
    print(f"💾 Đã lưu dữ liệu vào: {os.path.abspath(output_filename)}")
    print("=" * 80)

    return all_scraped_posts


def run_sample_verification():
    """
    Hàm kiểm thử độc lập parser DOM và công thức velocity_score với dữ liệu HTML mẫu chuẩn
    từ old.reddit.com để xác thực thuật toán ngay cả khi máy chủ Reddit bật Login Wall.
    """
    print("\n" + "=" * 80)
    print("🧪 CHẾ ĐỘ KIỂM THỬ XÁC MINH PARSER DOM (SAMPLE TEST)")
    print("=" * 80)
    
    # HTML giả lập chuẩn 100% cấu trúc của old.reddit.com
    current_ms = int(time.time() * 1000)
    sample_html = f"""
    <div class="thing id-t3_ad123 promoted link" data-fullname="t3_ad123" data-permalink="/comments/ad/">
        <a class="title">Bài quảng cáo được tài trợ (Phải bỏ qua)</a>
    </div>
    <div class="thing id-t3_gadget01 link" data-fullname="t3_gadget01" data-permalink="/r/gadgets/comments/g01/m4_macbook_pro_review/" data-timestamp="{current_ms - 2 * 3600 * 1000}">
        <div class="midcol unvoted">
            <div class="score unvoted" title="850">850</div>
        </div>
        <div class="entry unvoted">
            <p class="title"><a class="title may-blank" href="/r/gadgets/comments/g01/m4_macbook_pro_review/">Apple M4 Max MacBook Pro in-depth battery and performance benchmark</a></p>
            <ul class="flat-list buttons">
                <li><a class="bylink comments may-blank" href="...">124 comments</a></li>
            </ul>
        </div>
    </div>
    <div class="thing id-t3_bifl02 link" data-fullname="t3_bifl02" data-permalink="/r/BuyItForLife/comments/b02/cast_iron_pan_30_years/" data-timestamp="{current_ms - 10 * 3600 * 1000}">
        <div class="midcol unvoted">
            <div class="score unvoted" title="1420">1420</div>
        </div>
        <div class="entry unvoted">
            <p class="title"><a class="title may-blank" href="/r/BuyItForLife/comments/b02/cast_iron_pan_30_years/">My grandmother's Griswold cast iron skillet, still used daily after 60 years</a></p>
            <ul class="flat-list buttons">
                <li><a class="bylink comments may-blank" href="...">88 comments</a></li>
            </ul>
        </div>
    </div>
    <div class="thing id-t3_tiktok03 link" data-fullname="t3_tiktok03" data-permalink="/r/TikTokMadeMeBuyIt/comments/t03/viral_cleaning_gel/" data-timestamp="{current_ms - 15 * 60 * 1000}">
        <div class="midcol unvoted">
            <div class="score unvoted" title="210">210</div>
        </div>
        <div class="entry unvoted">
            <p class="title"><a class="title may-blank" href="/r/TikTokMadeMeBuyIt/comments/t03/viral_cleaning_gel/">This viral car vent cleaning putty actually works wonders!</a></p>
            <ul class="flat-list buttons">
                <li><a class="bylink comments may-blank" href="...">42 comments</a></li>
            </ul>
        </div>
    </div>
    <div class="thing id-t3_gadget04 link" data-fullname="t3_gadget04" data-permalink="/r/gadgets/comments/g04/hidden_score_post/" data-timestamp="{current_ms - 1 * 3600 * 1000}">
        <div class="midcol unvoted">
            <div class="score unvoted">●</div>
        </div>
        <div class="entry unvoted">
            <p class="title"><a class="title may-blank" href="/r/gadgets/comments/g04/hidden_score_post/">New open source e-ink monitor released with 60Hz refresh rate</a></p>
            <ul class="flat-list buttons">
                <li><a class="bylink comments may-blank" href="...">15 comments</a></li>
            </ul>
        </div>
    </div>
    """

    sample_posts = parse_old_reddit_dom(sample_html, "gadgets", "rising")
    print(f"✅ Bóc tách thành công {len(sample_posts)} bài viết từ HTML mẫu (Đã loại trừ bài promoted).")
    
    top_5_sample = sorted(sample_posts, key=lambda x: x["velocity_score"], reverse=True)
    print("\n🔥 TOP VELOCITY TỪ DỮ LIỆU MẪU:")
    for rank, p in enumerate(top_5_sample, 1):
        print(f"#{rank} [Velocity: {p['velocity_score']:>7.2f}] - {p['title'][:55]}... (Score: {p['score']}, Comm: {p['comments']}, Giờ: {p['hours_since_posted']}h)")

    with open("test_output.json", "w", encoding="utf-8") as f:
        json.dump(sample_posts, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Đã lưu dữ liệu mẫu vào test_output.json.")


def main():
    parser = argparse.ArgumentParser(description="Reddit Trend Scraper (curl_cffi + BeautifulSoup)")
    parser.add_argument(
        "--cookie",
        type=str,
        default=os.getenv("REDDIT_SESSION", ""),
        help="Giá trị cookie 'reddit_session' để vượt Login Wall nếu Reddit yêu cầu (mặc định đọc từ biến REDDIT_SESSION)",
    )
    parser.add_argument(
        "--test-sample",
        action="store_true",
        help="Chạy kiểm thử parser DOM và công thức velocity với dữ liệu HTML mẫu",
    )
    args = parser.parse_args()

    if args.test_sample:
        run_sample_verification()
        return

    # Chạy cào dữ liệu thực tế
    results = scrape_reddit(reddit_session_cookie=args.cookie if args.cookie else None)
    
    # Nếu kết quả rỗng do Reddit login wall, gợi ý người dùng cách kiểm thử
    if not results and not args.cookie:
        print("\n" + "*" * 80)
        print("ℹ️ LƯU Ý QUAN TRỌNG VỀ REDDIT LOGIN WALL:")
        print("  Reddit hiện tại chuyển hướng unauthenticated requests tới old.reddit.com sang:")
        print("  https://old.reddit.com/login/?reason=lor2")
        print("  Để test xác minh ngay parser DOM & công thức velocity, bạn có thể chạy:")
        print("      python test_reddit_scraper.py --test-sample")
        print("  Để cào dữ liệu thật từ tài khoản của bạn, chỉ cần truyền cookie:")
        print("      python test_reddit_scraper.py --cookie \"<GIÁ_TRỊ_COOKIE_REDDIT_SESSION>\"")
        print("*" * 80)


if __name__ == "__main__":
    main()
