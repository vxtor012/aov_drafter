# Phát triển, kiểm tra và triển khai

## Môi trường

- Python 3.10+ cho máy chủ tĩnh, crawler và kiểm tra dữ liệu.
- `requests` và `beautifulsoup4` cho crawler, cài từ `requirements.txt` trong `.venv`.
- Node.js có hỗ trợ `node --check` để kiểm tra cú pháp JS; không có dependency npm hoặc bước build.
- Trình duyệt hiện đại hỗ trợ ES6, CSS custom properties và `localStorage`.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
python -m http.server 8000 --bind 127.0.0.1 --directory public
```

Mở [http://localhost:8000](http://localhost:8000). Đường dẫn URL là `/assets/js/app.js`, `/assets/css/style.css` và `/assets/img/…`; không thêm tiền tố `/public/` vào URL khi đã phục vụ thư mục này. Khi sửa HTML/CSS/JS, tải lại trang; dùng hard refresh nếu thấy bản cũ. Trên macOS/Linux, dùng `.venv/bin/python` thay đường dẫn Python của Windows.

## Quy ước thay đổi

- Giữ UTF-8 để tránh hỏng tiếng Việt.
- Thay đổi dữ liệu bằng crawler và kiểm tra cả JSON/JS; phần `HERO_DATABASE` là dữ liệu sinh tự động, sẽ bị ghi đè lần cập nhật sau.
- Sửa tên khác biệt trong `AOV_TO_ROVMETA`, tên khắc chế cũ trong `UNMATCHED_REPLACEMENTS`, ngoại lệ đường trong `ROLE_OVERRIED`.
- Quy tắc khắc chế thủ công nằm ở `COUNTERS_MANUAL`; dùng ID có thật và giải thích ngắn, có thể kiểm chứng.
- Khi đổi thuật toán ở `calculateSuggestions`, cập nhật bảng điểm trong `ARCHITECTURE.md`.
- Không commit `.venv`, cache Python hoặc log chứa thông tin môi trường cá nhân.

## Kiểm tra tự động

```powershell
.\.venv\Scripts\python.exe scripts/validate_data.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m py_compile scripts/crawler_system.py scripts/validate_data.py
node --check public/assets/js/app.js
```

Validator chỉ dùng thư viện chuẩn Python. Nó kiểm tra ID duy nhất, vai trò/tier, tỷ lệ hữu hạn 0–100, thuộc tính nguyên 1–5, counter hợp lệ và dữ liệu JSON/JS giống nhau. Bộ unittest kiểm tra thêm dữ liệu lỗi, tham chiếu Next.js lồng nhau và việc giữ snapshot khi mạng lỗi ở bước danh sách. Unittest cần thư viện crawler đã cài, không gọi mạng thật.

Các kiểm tra này chưa xác minh tính đúng của số liệu nguồn, bản quyền nội dung, hiển thị CSS hoặc toàn bộ luồng thao tác trình duyệt.

## Kiểm tra trình duyệt tự động

Cài thư viện phát triển và trình duyệt thử nghiệm, sau đó chạy khi máy chủ tại cổng 8000 đang mở:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe tests/ui_smoke.py
```

Có thể đặt `UI_BASE_URL` để dùng URL khác. Nếu muốn dùng Edge/Chrome đã cài thay cho Chromium của Playwright, đặt `UI_BROWSER_PATH` bằng đường dẫn tuyệt đối tới executable trình duyệt. Script chạy headless, kiểm tra tìm kiếm không dấu, bộ lọc, gợi ý, theme, hoàn tác/reset, 20 lượt cấm/chọn, dialog và mobile. Ảnh kết quả nằm trong `.taste-skill/qa/` (không commit).

## Kiểm tra giao diện thủ công

1. Tải mới trang, kiểm tra console không có lỗi JavaScript và lưới tướng xuất hiện.
2. Tìm `Evita`, lọc Mid và chọn tướng; xác nhận đúng đội đến lượt, tướng không chọn lại được.
3. Chuyển Meta/Khắc chế, lọc vai trò gợi ý và đổi các kiểu sắp xếp.
4. Hoàn tác rồi chọn lại; **Draft mới**, mở **Tùy chọn** và tắt bỏ qua cấm để đi qua 10 lượt cấm.
5. Chọn đủ 5 tướng mỗi đội; kiểm tra tổng kết, đóng overlay và bắt đầu trận mới.
6. Mở **Tùy chọn**, đổi theme, tải lại để kiểm tra lưu tùy chọn; xác nhận đội hình không được giữ sau tải lại.
7. Kiểm tra cửa sổ hẹp và màn hình desktop; thử khi ảnh ngoài bị lỗi để xác nhận fallback.

## Triển khai

Đây là website tĩnh. Cấu hình thư mục publish/document root là `public`, không cần lệnh build. Khi tải tệp lên hosting, đưa **nội dung bên trong `public/`** vào thư mục gốc của website: `index.html` và `assets/`. Giữ nguyên đường dẫn tương đối và UTF-8. Dữ liệu tướng đã được nhúng trong `assets/js/app.js`; các thư mục `data/`, `scripts/`, `tests/`, `docs/`, `.agents/`, `.venv/` và `.git/` không cần được phục vụ công khai.

Không có lệnh deploy được cấu hình sẵn hoặc workflow CI trong repository. Việc cập nhật dữ liệu trên máy không tự cập nhật hosting: kiểm tra, đưa các tệp đã đồng bộ vào cùng bản phát hành rồi triển khai bằng công cụ hosting đang sử dụng. Không dùng `http.server` làm máy chủ production.

## Xử lý lỗi

| Triệu chứng | Cách xử lý |
| --- | --- |
| `ModuleNotFoundError: requests` hoặc `bs4` | Cài `requirements.txt` bằng Python trong `.venv`; chạy crawler bằng chính Python đó |
| PowerShell không cho kích hoạt venv | Dùng trực tiếp `.\.venv\Scripts\python.exe`, không cần thay ExecutionPolicy |
| Tạo venv lỗi `ensurepip` | Kiểm tra bản cài Python có pip/venv; có thể dùng `uv venv .venv` và `uv pip install --python .venv/Scripts/python.exe -r requirements.txt` nếu đã cài uv |
| Kết nối timeout, proxy, 403/429 | Kiểm tra mạng/proxy, chờ rồi thử lại; kiểm tra nguồn còn hoạt động, tránh chạy crawler liên tục |
| Không đọc được `tiers` hoặc guard dừng | Nguồn có thể đổi cấu trúc; kiểm tra HTML thật và parser trước khi cập nhật |
| JSON/JS không đồng bộ | Chạy lại crawler thành công hoặc khôi phục cả hai tệp cùng phiên bản; chạy validator |
| Tướng mới sai đường hoặc không có chỉ số | Kiểm tra ánh xạ tên, ngoại lệ vai trò và `fallback_rate_fields` trong báo cáo |
| Ảnh hoặc font không tải | Kiểm tra mạng/CDN; ảnh tướng có SVG dự phòng; font ngoài không được đóng gói cục bộ, icon giao diện dùng SVG nội tuyến |
| Tải lại mất đội hình | Hành vi hiện tại: chỉ theme và tùy chọn bỏ qua cấm được lưu |
