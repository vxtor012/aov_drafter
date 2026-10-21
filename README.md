# AOV Drafter

Ứng dụng web hỗ trợ cấm/chọn tướng Liên Quân Mobile (Arena of Valor), gợi ý đội hình theo meta và quan hệ khắc chế. Giao diện tiếng Việt, chạy trực tiếp trên trình duyệt bằng HTML, CSS và JavaScript; không cần backend, tài khoản hay bước build.

## Tính năng

- Mô phỏng hai đội Xanh/Đỏ, tối đa 5 lượt cấm và 5 lượt chọn mỗi đội.
- Chuỗi chọn theo nhóm **1–2–2–2–2–1**; có thể bỏ qua lượt cấm.
- Tìm tướng theo tên, lọc Top/Rừng/Mid/AD/SP, sắp xếp theo tên, tier hoặc tỷ lệ thắng/chọn/cấm.
- Hai chế độ gợi ý **Meta** và **Khắc chế**, hiển thị tối đa 6 lựa chọn cùng lý do cộng/trừ điểm.
- Phân tích sát thương, chống chịu, cơ động, giao tranh và đẩy lẻ của đội hình; tổng kết khi chọn đủ tướng.
- Hoàn tác, đặt lại và giao diện sáng/tối/theo hệ thống.
- [Trang tốc đánh](public/attack-speed.html): chọn ảnh tướng để tra model C/E/F/G/H/H-1f và các mốc phần trăm theo frame. Có nguồn theo từng tướng, ghi chú ngoại lệ và phần đối chiếu; không tự gán model cho tướng chưa có dữ liệu.

## Chạy nhanh

Yêu cầu Python 3.10+ để mở máy chủ tĩnh hoặc cập nhật dữ liệu. Node.js chỉ cần khi kiểm tra cú pháp JavaScript.

```powershell
git clone https://github.com/vxtor012/aov_drafter.git
cd aov_drafter
python -m http.server 8000 --bind 127.0.0.1 --directory public
```

Mở [http://localhost:8000](http://localhost:8000). Nhấn `Ctrl+C` để dừng. Python chỉ phục vụ tệp tĩnh, không chạy crawler khi người dùng mở trang.

Trang tốc đánh ở [http://localhost:8000/attack-speed.html](http://localhost:8000/attack-speed.html). Chọn ảnh tướng và trạng thái để xem cột breakpoint tương ứng; trên mobile tự chuyển sang tab bảng frame. Xem [nguồn và giới hạn dữ liệu tốc đánh](docs/ATTACK_SPEED.md).

Có thể mở `public/index.html` trực tiếp để xem nhanh, nhưng nên dùng HTTP để hành vi lưu tùy chọn và tải tài nguyên ổn định hơn. Ảnh tướng và Google Fonts cần kết nối mạng; biểu tượng giao diện được vẽ bằng SVG nội tuyến.

## Cách sử dụng

1. Mở **Tùy chọn** để bật/tắt **Bỏ qua lượt cấm** trước khi chọn tướng. Mặc định vào thẳng lượt chọn.
2. Xem đội đang đến lượt trên thanh trạng thái; bấm thẻ tướng để cấm/chọn cho đội đó.
3. Dùng bộ lọc vai trò và chuyển **Meta/Khắc chế** để xem gợi ý phù hợp.
4. Dùng **Hoàn tác** nếu chọn nhầm, **Draft mới** để bắt đầu lại. Nhấn `/` để tìm tướng nhanh.
5. Mở **Xem lý do** trên từng gợi ý để xem điểm chi tiết. Sau 10 lượt chọn, xem **Tổng kết** để so sánh đội hình và các kèo đối đầu. Trên mobile, chuyển tab **Tướng/Gợi ý** để thao tác.

Chỉ giao diện (`theme`) và tùy chọn bỏ qua cấm (`skipBanPhase`) được lưu trong `localStorage`. Đội hình đang chọn và lịch sử hoàn tác nằm trong bộ nhớ, sẽ mất khi tải lại trang. Tìm kiếm không phân biệt chữ hoa/thường và dấu tiếng Việt. Giao diện mặc định tối, có thể đổi sang sáng hoặc theo hệ thống trong **Tùy chọn**.

## Dữ liệu hiện tại

Snapshot thu thập ngày **21/10/2026** có **130 tướng**, trong đó lane và meta ranked lấy từ RoVGuide với dữ liệu chốt **19/10/2026**; **30 tướng có nhiều lane**. Có **93** trang khắc chế chi tiết và **931** liên kết khắc chế. Báo cáo nguồn cho từng tướng nằm trong [`data/data_update_report.json`](data/data_update_report.json).

Nguồn ranked chính là [RoVGuide](https://rovguide.com/meta), hiện hiển thị thống kê xếp hạng máy chủ Thái và dữ liệu thi đấu chuyên nghiệp riêng. Lane cũng lấy từ hồ sơ RoVGuide; [RovMeta](https://rovmeta.com/) là nguồn đối chiếu và khắc chế dự phòng. [AOV Builds](https://aov-builds.com/tuong/) cung cấp roster/ảnh và khắc chế cộng đồng. Các chỉ số ranked này không đại diện cho máy chủ Việt Nam; ứng dụng hiển thị vùng và ngày chụp ngay trong chế độ Meta. Garena Việt Nam được giữ làm nguồn đối chiếu patch, không ghi đè dữ liệu meta Thái.

Các thuộc tính 1–5 vẫn là **ước lượng theo lane** và không được dùng trong engine gợi ý pick. Điểm là thứ tự tham khảo từ meta ranked, độ phủ lane và quan hệ khắc chế; đây không phải xác suất thắng. Xem [nguồn dữ liệu và quy trình cập nhật](docs/DATA.md) cùng [mô hình tính điểm](docs/ARCHITECTURE.md).

## Cập nhật dữ liệu

Chạy từ thư mục dự án, trong PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/crawler_system.py
.\.venv\Scripts\python.exe scripts/validate_data.py
```

Không cần kích hoạt môi trường ảo. Trên macOS/Linux, thay `.\.venv\Scripts\python.exe` bằng `.venv/bin/python`.

Crawler ghi ba tệp: `data/crawled_heroes.json`, khối `HERO_DATABASE` trong `public/assets/js/app.js`, và `data/data_update_report.json`. Luôn xem báo cáo và diff trước khi đưa dữ liệu lên hosting. Trình duyệt không tự cập nhật dữ liệu từ Internet.

## Cấu trúc dự án

```text
.
├── public/                     # Thư mục gốc của website khi chạy/triển khai
│   ├── index.html              # Điểm vào ứng dụng
│   └── assets/
│       ├── css/style.css       # Bố cục, theme và hiệu ứng
│       ├── js/app.js           # Dữ liệu nhúng, trạng thái và gợi ý
│       └── img/                # Logo và ảnh nền cục bộ
├── data/
│   ├── crawled_heroes.json     # Snapshot tướng
│   └── data_update_report.json # Nguồn, thời gian và trường dự phòng
├── scripts/
│   ├── __init__.py
│   ├── crawler_system.py       # Thu thập và đồng bộ dữ liệu
│   └── validate_data.py        # Kiểm tra schema và đồng bộ JSON/JS
├── tests/                      # Kiểm thử dữ liệu, crawler và đường dẫn
├── docs/                       # Kiến trúc, dữ liệu và phát triển
├── requirements.txt            # Thư viện Python của crawler
├── requirements-dev.txt        # Thư viện kiểm thử trình duyệt
├── skills-lock.json            # Khóa phiên bản skill phát triển
└── README.md
```

Chỉ phục vụ hoặc triển khai nội dung `public/`. Các thư mục `data/`, `scripts/`, `tests/`, `docs/`, `.agents/` và `.venv/` nằm ngoài thư mục website. Dữ liệu JSON được crawler nhúng vào JavaScript trước khi triển khai.

## Tài liệu và kiểm tra

- [Kiến trúc và thuật toán gợi ý](docs/ARCHITECTURE.md)
- [Schema, nguồn và cập nhật dữ liệu](docs/DATA.md)
- [Phát triển, kiểm thử, triển khai và xử lý lỗi](docs/DEVELOPMENT.md)
- [Hướng thiết kế giao diện và các nguồn tham khảo](docs/UI_DESIGN.md)

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
node --check public/assets/js/app.js
```

Các kiểm tra trên xác minh dữ liệu, đồng bộ JSON/JS và một số nhánh lỗi crawler; không thay thế kiểm tra giao diện trên trình duyệt.

## Giấy phép và ghi nhận

Repository hiện chưa có tệp `LICENSE`; không mặc định suy ra giấy phép mã nguồn mở. Tên game, hình ảnh và nội dung nguồn thuộc chủ sở hữu tương ứng. Khi phân phối dữ liệu hoặc sử dụng thương mại, cần kiểm tra quyền sử dụng từ từng nguồn. Dự án là công cụ tham khảo cộng đồng, không phải sản phẩm chính thức của Garena/TiMi.
