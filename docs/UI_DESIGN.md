# Giao diện draft

## Mục tiêu

Câu hỏi chính của màn hình: **Đến lượt đội nào, và nên chọn tướng nào?** Hai đội phải đọc được ngay; danh sách tướng là vùng thao tác lớn nhất, phân tích là phần hỗ trợ.

Đối tượng dữ liệu thật gồm 130 tướng với ảnh đại diện, hai đội năm người, tối đa năm lượt cấm mỗi đội, chuỗi chọn 1–2–2–2–2–1, năm vị trí và sáu gợi ý. Không thêm số liệu, tính năng tài khoản hoặc phòng draft giả vào giao diện.

## Nguồn tham khảo

Đã tham khảo ngày 21/10/2026:

- [ProComps](https://procomps.gg/): mô tả và hình giới thiệu trợ lý draft, gợi ý theo vị trí, nhu cầu đội hình và phân tích. Áp dụng cách đặt phân tích ở vai trò hỗ trợ quyết định, thay vì dàn mọi chỉ số lên từng thẻ. Không sao chép giao diện landing page vào công cụ.
- [Drafter.lol](https://drafter.lol/) và [Broadcaster Guide](https://drafter.lol/broadcasters): phân biệt picks/bans, tên đội và lượt với phần điều khiển phụ; hướng dẫn Stream Mode giải thích rõ nội dung nào được giữ và ẩn. Áp dụng phân cấp đó cho bảng hai đội và menu tùy chọn. Draft Prep yêu cầu đăng nhập nên phần này không được khảo sát bên trong tài khoản.
- [DraftDiff](https://draftdiff.io/): xem mẫu draft được trình bày trên trang công khai, tham khảo cách nhóm chân dung theo hai đội. Trang hiện tại thiên về sản xuất broadcast, không xem đó là toàn bộ giao diện công cụ draft.

Đây là tham khảo cấu trúc thông tin. Không tải lại ảnh tướng LoL, logo hoặc mã nguồn của các sản phẩm trên.

## Quyết định thiết kế

- Giữ HTML/CSS/JavaScript thuần để tiếp tục triển khai trên GitHub Pages.
- Dùng hướng `true-black-flat`, seed `102691671`, từ skill `design-taste-frontend`; giữ font Be Vietnam Pro có hỗ trợ tiếng Việt. Chọn bố cục builder không có sidebar vì sản phẩm chỉ có một màn hình thao tác.
- Nền đen, panel trung tính theo bậc sáng; không ảnh nền, gradient, blur, glow hoặc bóng đổ trang trí. Có theme sáng và theo hệ thống; mặc định tối khi chưa lưu lựa chọn.
- Bản sắc nằm ở ảnh tướng Liên Quân và bảng hai đội năm ô. Xanh/đỏ chỉ nhận diện đội, lượt đang chạy và dữ liệu phân tích; tier dùng nhãn trung tính.
- Bảng đội hình nằm ngang ở trên. Lượt hiện tại có văn bản và tiến độ thật; khi bỏ qua cấm, lượt chọn bắt đầu từ 1/10.
- Pool tướng ở cột rộng, gợi ý ở cột 362px. Trên màn hình nhỏ hơn 880px, hai vùng chuyển thành tab Tướng/Gợi ý; dưới 600px, hai đội xếp dọc và pool có bốn cột.
- Thẻ tướng chỉ giữ ảnh, tên, tier và trạng thái đã dùng. Bỏ tỷ lệ thắng lặp trên mọi thẻ và mini-stat trong ô đội hình. Tỷ lệ vẫn được dùng trong sắp xếp/tính điểm và có trong lý do khi áp dụng.
- Mỗi gợi ý có vai trò, tier, điểm, hành động Chọn và một lý do ngắn. Các giải thích dài nằm trong `details`, mở bằng Xem lý do.
- Giữ Hoàn tác và Draft mới ở thanh trên; theme và bỏ qua cấm nằm trong Tùy chọn. Tổng kết hỗ trợ mở lại, đóng bằng Escape, giữ focus bàn phím trong dialog và khôi phục focus khi đóng.
- Thẻ tướng là button thật, có tên truy cập, trạng thái disabled và focus rõ. Tìm kiếm hỗ trợ tiếng Việt không dấu cùng phím `/`; lỗi ảnh được thay bằng SVG trung tính.

## Kiểm tra

Bản trước có 5 lỗi và 5 cảnh báo trong lần kiểm tra thiết kế tự động: chữ nhãn nhỏ/in hoa, gradient chữ, bóng/glow, tương phản và phân bố không gian. Sau refactor, kiểm tra desktop 1440px, tablet 768px và mobile 390px; xem cả trạng thái trống, đội hình có tướng, theme sáng và bảng tổng kết.

Lần kiểm tra inspector cuối đạt **0 lỗi, 0 cảnh báo**, so với **5 lỗi, 5 cảnh báo** của bản trước. Không redraw hướng thiết kế; màu xanh/đỏ giữ vai trò nhận diện hai đội thay cho accent trang trí. Không có dữ liệu mẫu cần thay thế.

`tests/ui_smoke.py` kiểm tra thao tác bằng Playwright: tìm kiếm/bộ lọc/sắp xếp, đổi chế độ/vị trí gợi ý, chọn nhanh, theme lưu sau reload, 10 lượt cấm và 10 lượt chọn, hoàn tác/reset, tab mobile, không tràn ngang tại 360/390/600/768/1024px và focus dialog. Ảnh kiểm tra nằm trong `.taste-skill/qa/`, ảnh inspector trong `.taste-skill/` và không commit.
