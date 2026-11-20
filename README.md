# 📡 Reddit Trend Velocity Radar 2.0

Hệ thống bóc tách dữ liệu xu hướng, săn trend sản phẩm và tính toán chỉ số lan truyền (**Velocity Score**) trên Reddit thời gian thực mà **KHÔNG cần dùng Reddit API** hay trình duyệt ảo (Selenium/Playwright).

---

## ✨ Điểm Nổi Bật & Cải Tiến

1. **Chuẩn hóa Link mở trực tiếp (Cách 1)**:
   - Toàn bộ liên kết bài viết được chuẩn hóa theo định dạng `https://old.reddit.com/...` giúp người dùng tại Việt Nam bấm vào mở trực tiếp được ngay mà không bị nhà mạng (Viettel, VNPT, FPT) chặn DNS (khắc phục hoàn toàn lỗi `ERR_CONNECTION_REFUSED`).
2. **Kiến trúc tách rời độc lập (Modular Architecture)**:
   - **Backend**: FastAPI + `curl_cffi` (impersonate `chrome120`) + `BeautifulSoup` (parser `lxml`) + `Pydantic`.
   - **Frontend**: React 19 + TypeScript + Vite + Lucide Icons + Custom High-Contrast Observatory Design System.
   - Các module được bóc tách rõ ràng: `dom_parser`, `scraper_engine`, `storage`, `routes`, `components`, `services`.
3. **Quản lý Subreddit linh hoạt trên UI**:
   - Thêm/bớt subreddit tùy ý với phím Enter, không còn lo bị lỗi `HTTP 404` khi nhập phải subreddit không tồn tại (như `TikTokMadeMeBuyIt`).
   - Tích hợp sẵn các Preset săn trend thông minh:
     - *Đồ bền & Độc lạ*: `BuyItForLife`, `gadgets`, `DidntKnowIWantedThat`
     - *Viral Shopping*: `TikTokshop`, `AmazonWTF`, `shutupandtakemymoney`
     - *Công nghệ & Đổi mới*: `gadgets`, `technology`, `hardware`
4. **Live Scrape Console & Quản lý Cookie**:
   - Giao diện Terminal theo dõi tiến trình cào theo thời gian thực (hiển thị mã HTTP 200, 302, 404, 429 và bộ đếm thời gian nghỉ 2–4s).
   - Modal cấu hình Cookie `reddit_session` với hướng dẫn trực quan để vượt Login Wall `reason=lor2`.

---

## 🎨 Trend → Ý tưởng sản phẩm POD (thị trường Mỹ, OpenAI)

1. Cài thư viện: `pip install -r requirements.txt`
2. Sao chép `.env.example` thành `.env` và điền `OPENAI_API_KEY=sk-...` (tùy chọn `OPENAI_MODEL`, mặc định `gpt-5-mini`). File `.env` đã được `.gitignore`.
3. Tab **Bài viết**: bấm preset **Trend POD Mỹ** (`popular`, `OutOfTheLoop`, `soccer`, `nfl`, `nba`, `movies`, `television`, `gaming`, `Music`, `memes`, `popculturechat`) → cào dữ liệu.
4. Tab **Trend → POD**:
   - **Phát hiện trend**: LLM gom các bài ≤48h (top 200 theo velocity) thành trend; điểm trend = tổng velocity × số subreddit cùng nhắc (tính bằng code). Trend không hợp POD (thảm họa, chính trị...) bị ẩn mặc định.
   - **Tạo ý tưởng POD**: 3–5 concept (sản phẩm, slogan tiếng Anh, mô tả hình, phong cách, màu, **prompt cho designer**, từ khóa SEO) + **cảnh báo bản quyền/thương hiệu**.
   - **Xuất CSV cho designer**.

Kết quả được lưu ở `trends.json`. API: `GET /api/trends`, `POST /api/trends/detect`, `POST /api/trends/{id}/ideas`, `GET /api/trends/export`.

> ⚠️ Luôn kiểm tra lại rủi ro IP trước khi đăng bán: không dùng tên/logo giải đấu, đội, phim, nhân vật, người thật.

---

## 🚀 Cách Khởi Chạy Ứng Dụng (Nhanh Nhất)

### Cách 1: Chạy file Python duy nhất
Mở PowerShell hoặc Command Prompt tại thư mục dự án và chạy:
```powershell
python run_app.py
```
*(Hệ thống sẽ tự động bật backend và mở trình duyệt web đến địa chỉ: `http://127.0.0.1:8000`)*

### Cách 2: Nhấp đúp file Batch (Windows)
Nhấp đúp chuột vào file:
```text
start_app.bat
```

---

## 🛠️ Phát Triển Độc Lập (Development Mode)

Nếu bạn muốn chỉnh sửa code riêng cho Backend hoặc Frontend:

### 1. Khởi động Backend (FastAPI):
```powershell
python -m backend.main
```
- Endpoint Backend: `http://127.0.0.1:8000`
- Swagger API Docs: `http://127.0.0.1:8000/docs`

### 2. Khởi động Frontend (React Dev Server):
```powershell
cd frontend
npm run dev
```
- Giao diện Dev: `http://localhost:5173` (đã được cấu hình tự động proxy các request `/api` sang Backend port 8000).

### 3. Build lại Frontend khi thay đổi giao diện:
```powershell
cd frontend
npm run build
```

---

## 📁 Cấu Trúc Thư Mục Dự Án

```text
D:\trend_data\
├── backend\
│   ├── config.py              # Cấu hình tập trung, default subreddits, headers
│   ├── schemas.py             # Pydantic models cho request, response, stats
│   ├── services\
│   │   ├── dom_parser.py      # Bóc tách DOM BeautifulSoup, công thức Velocity
│   │   ├── scraper_engine.py  # Động cơ cào curl_cffi, đa luồng, rate limit, logging
│   │   └── storage.py         # Quản lý đọc ghi JSON, bộ lọc bài viết, thống kê
│   ├── routes\
│   │   ├── scrape_routes.py   # API điều khiển cào dữ liệu (start, status, cancel)
│   │   ├── posts_routes.py    # API truy vấn bài viết, thống kê, xuất JSON
│   │   └── settings_routes.py # API quản lý cookie session & danh sách subreddit
│   └── main.py                # FastAPI entry point & Static files server
│
├── frontend\
│   ├── src\
│   │   ├── components\
│   │   │   ├── Navbar.tsx           # Header, nút hành động, trạng thái cookie
│   │   │   ├── StatsCards.tsx       # 4 thẻ chỉ số thống kê thị trường
│   │   │   ├── SubredditConfig.tsx  # Quản lý tags subreddit & presets
│   │   │   ├── PostTable.tsx        # Bảng dữ liệu mật độ cao & link old.reddit
│   │   │   ├── PostCardGrid.tsx     # Chế độ xem thẻ bài trực quan
│   │   │   ├── CookieModal.tsx      # Modal nhập cookie reddit_session
│   │   │   └── ScrapeConsole.tsx    # Live terminal log tiến trình cào
│   │   ├── services\api.ts          # Giao tiếp HTTP client với backend
│   │   ├── types\index.ts           # TypeScript interfaces
│   │   ├── App.tsx                  # Root component kết nối logic
│   │   └── index.css                # Hệ thống CSS Observatory Theme
│   ├── dist\                        # Bản build tối ưu đã sẵn sàng chạy
│   └── package.json
│
├── test_reddit_scraper.py     # Script CLI độc lập (đã cập nhật Cách 1)
├── test_output.json           # File lưu trữ dữ liệu cào được
├── run_app.py                 # File chạy trọn gói Backend + Frontend
└── start_app.bat              # Phím tắt click-to-run trên Windows
```
