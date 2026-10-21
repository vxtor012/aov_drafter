# Tra cứu model tốc đánh

`public/attack-speed.html` chỉ có lưới ảnh tướng và bảng breakpoint. Chọn tướng rồi chọn dạng để tô cột tương ứng; mobile tự chuyển sang bảng frame. Có tìm kiếm, lọc model, nguồn và ghi chú cho từng tướng. Không có form tính, nhập chỉ số, dialog hoặc đề xuất lên đồ.

## Mức độ xác minh

Rà soát tài liệu ngày **21/10/2026**. `verified_game_patch` hiện là `null`: chưa đo lại trong client Việt Nam, chưa có bảng chính thức xác nhận toàn bộ các ngưỡng. Ngày đăng bài và ngày rà soát không phải ngày đo. Bài tổng hợp 2026 cũng không biến số liệu đo từ năm trước thành phép đo mới.

Registry nguồn nằm trong `data/attack_speed_models.json`, gồm:

| Nguồn | Ngày | Dùng để |
| --- | --- | --- |
| [AoV Tactics & Guides](https://www.facebook.com/aovtacticsguides/posts/1083295804615977/) | 10/10/2026 | Mapping / bảng tham khảo mới nhất tìm được; tổng hợp AOVTW |
| [Bahamut · hao940322](https://forum.gamer.com.tw/Co.php?bsn=30518&sn=279260) | sửa 02/04/2024 | Bảng gốc; bổ sung F chậm |
| [Bahamut · bigbirdno1](https://forum.gamer.com.tw/Co.php?bsn=30518&sn=333724) | sửa 21/07/2025 | Cập nhật đo từng tướng / ngoại lệ |
| [Phản hồi #12 trong cùng chủ đề](https://forum.gamer.com.tw/C.php?bsn=30518&gothis=279260&page=1&snA=54503) | 22/07/2025 | Báo thêm mốc Preyta, chưa có bảng đầy đủ |
| [Thử riêng Thorne](https://forum.gamer.com.tw/C.php?bsn=30518&gothis=335381&page=1&snA=61173) | chưa xác định | Đối chiếu một phần, có khác biệt khi di chuyển |
| [Cokou32556](https://forum.gamer.com.tw/Co.php?bsn=30518&sn=245374) | 22/03/2022 | Lịch sử; có mapping khác, không ghi đè bản mới |
| [PTT · Nouis](https://www.ptt.cc/bbs/ArenaOfValor/M.1557855415.A.108.html) | 15/05/2019 | Kết quả cũ trái chiều, không xác nhận cho bản hiện tại |
| [Garena RoV · Capheny](https://www.rov.in.th/hero/capheny) | trang không ghi ngày | Cơ chế riêng, không phải bảng frame |
| [Garena Taiwan · Stuart](https://moba.garena.tw/news/show/4377) | 03/11/2023 | Đối chiếu định danh sau làm lại, không xác nhận breakpoint |

Các bản tổng hợp và phản hồi trong cùng chuỗi AOVTW được lưu cùng `family`. Không đếm chúng thành nhiều phép đo độc lập cho toàn bộ roster. Nguồn chính thức chỉ hỗ trợ đúng cơ chế/định danh đã nêu, không chứng thực model số học.

## Cách giữ dữ liệu thận trọng

- Tướng không có trong nguồn: `unknown`, không tự gán C theo lane/class.
- Mỗi tướng có `evidence`; mỗi dòng frame có `sources`. F ở 25–20 frame chỉ dẫn bảng 2024. H-1f không suy thêm dòng 5 frame.
- Preyta giữ E làm tham khảo nhưng có `status: partial`; báo cáo mốc ngoài E chưa đủ để thêm một dòng số chính xác. Ghi chú hiện ngay khi chọn.
- Fennik, Heino, Butterfly, Marja thiếu bảng riêng đầy đủ: giữ tham chiếu/ghi chú, không tô cột chuẩn như kết quả chắc chắn.
- Có dạng riêng cho Yena, Celica, Liliana, Wisp và Volkath. Sinestrea (蘇離) khác Stuart (森圖爾特); đối chiếu tên đa ngôn ngữ để tránh ghép nhầm.
- Bảng chỉ tra ngưỡng đánh thường. Không dùng để suy trực tiếp DPS, FPS thiết bị, kỹ năng hoặc cách hủy động tác.

## Bảo trì

Sửa nguồn, bảng hoặc mapping ở `data/attack_speed_models.json` và ghi lý do theo bằng chứng. Chạy:

```powershell
.\.venv\Scripts\python.exe scripts/build_attack_speed_data.py
node tests/attack_speed.test.cjs
```

Builder dùng Python chuẩn, lấy ID/tên/ảnh từ roster hiện tại và xuất `public/assets/js/attack-speed-data.js`. Workflow Pages chạy builder trước deploy, gắn hash JS/CSS để tránh cache. Đây là bước đóng gói dữ liệu đã duyệt, **không tự tải và xác minh số đo mới**. Chỉ cập nhật ngày rà soát khi thực sự đọc lại tài liệu; không tự điền patch hoặc ngày đo.

Kiểm thử giao diện: phục vụ `public/`, rồi chạy `tests/attack_speed_ui.py`. Có thể đặt `UI_BROWSER_PATH` để dùng Edge/Chrome có sẵn. Test kiểm tra chọn tướng/dạng, ngoại lệ, nguồn, tìm/lọc, theme, điều hướng, không có form tính và ba kích thước màn hình.
