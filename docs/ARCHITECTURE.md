# Kiến trúc và thuật toán

Trang tra cứu tốc đánh `public/attack-speed.html` hoạt động độc lập, không nạp `app.js` hoặc khởi tạo draft. Mapping, bảng frame và nguồn sinh trong `attack-speed-data.js`; `attack-speed.js` xử lý chọn tướng, đổi dạng và tô cột model. Trang không có bộ tính hoặc form nhập tốc đánh. Xem [nguồn và các ngoại lệ](ATTACK_SPEED.md).

## Thành phần và luồng dữ liệu

```text
 AOV Builds ── roster, ảnh, khắc chế ────────────┐
 RoVGuide ──── lane, ranked Thái Lan ────────────┼── scripts/crawler_system.py
 RovMeta ───── counter dự phòng/đối chiếu ───────┤        │
 Garena VN ─── đối chiếu patch ──────────────────┘        ├── data/crawled_heroes.json
                                                          ├── public/assets/js/app.js
                                                          └── data/data_update_report.json

public/ ── máy chủ tĩnh ── trình duyệt ── thao tác draft và gợi ý
```

Không có API backend hoặc database server. Frontend đọc hằng `HERO_DATABASE` nhúng trong `public/assets/js/app.js`; tệp JSON phục vụ kiểm tra và bảo trì, không được frontend `fetch` lúc chạy. Muốn thay dữ liệu hiển thị phải đồng bộ cả hai bản rồi tải lại trang.

## Trạng thái và lượt chơi

`TURN_SEQUENCE` gồm 20 bước: 10 bước cấm xen kẽ Xanh/Đỏ, sau đó 10 bước chọn theo thứ tự đội Xanh, Đỏ, Đỏ, Xanh, Xanh, Đỏ, Đỏ, Xanh, Xanh, Đỏ. Đây là quy tắc mô phỏng của ứng dụng, không phải cam kết cập nhật mọi chế độ thi đấu hiện hành.

`state` chứa chỉ số lượt, bốn mảng cấm/chọn, bộ lọc, kiểu sắp xếp, chế độ gợi ý và lịch sử. Mỗi mảng đội có 5 vị trí. `handleHeroSelect` ghi snapshot lịch sử trước khi đổi trạng thái; `handleUndo` khôi phục snapshot, `handleReset` tạo lại lượt đầu theo tùy chọn bỏ qua cấm.

Khi khởi động, `DOMContentLoaded` gắn sự kiện, nạp theme/tùy chọn cấm và gọi `renderUI`. Các hàm `renderHeroGrid`, `renderRecommendationsAndStats`, `renderPickCol` cập nhật DOM. Tướng đã cấm/chọn bị loại khỏi tập gợi ý và vô hiệu hóa trên lưới.

## Tính điểm gợi ý

`calculateSuggestions(teamType)` loại tướng đã cấm/chọn, gán mỗi lượt chọn hiện tại vào tối đa một lane để lane phụ không lấp nhiều vị trí cùng lúc, rồi chấm từng ứng viên theo các tín hiệu có nguồn. Bộ lọc lane xét cả lane chính và phụ. Trả tối đa 6 lựa chọn.

Mọi chế độ bắt đầu từ 45 điểm. Các điểm thành phần đều hiện trong lý do và tổng bị giới hạn trong 0–100. Điểm dùng để xếp hạng lựa chọn; không phải xác suất thắng.

| Thành phần | Meta | Khắc chế |
| --- | --- | --- |
| Tier ranked `S+ / S / A / B / C` | `+8 / +5 / +2 / −2 / −5` | 25% điểm tier, làm tròn |
| WR (so với 50%) | `(WR−50)×1.2`, giới hạn ±8 | Không dùng |
| Tần suất pick + ban | `(PR+BR−10)×0.15`, giới hạn −2 đến +4 | Không dùng |
| Lane chính còn thiếu | +10 | +10 |
| Chỉ phù hợp lane phụ còn thiếu | +6 | +6 |
| Khắc chế biên tập thủ công | +6 mỗi đối thủ, tổng khắc chế tối đa +16 | +8 mỗi đối thủ, tối đa +20 |
| Khắc chế trong nguồn | +3 mỗi đối thủ, tổng khắc chế tối đa +16 | +5 mỗi đối thủ, tối đa +20 |
| Ứng viên bị khắc chế theo dữ liệu | −4 mỗi đối thủ, tối đa −12 | −5 mỗi đối thủ, tối đa −12 |

WR/PR/BR là phần trăm, ví dụ `52.5`, lấy từ ranked máy chủ Thái Lan. Tier và tỷ lệ giảm nửa trọng số sau 30 ngày, rồi ngừng cộng sau 90 ngày. Chế độ Khắc chế giữ tier ở trọng số nhỏ để gợi ý lane/matchup chi phối; không cộng tỷ lệ meta lần nữa. Counter link là tín hiệu đối đầu được nguồn ghi nhận, không phải chênh lệch win rate đo được.

Engine bỏ các điểm bù chống chịu/sát thương/cơ động/giao tranh vì thuộc tính hiện có chỉ là ước lượng theo lane, bỏ danh sách "tank shredder" cố định và các điểm +1 không được giải thích. Không còn cộng điểm cướp bài theo vai trò địch hoặc nhiều lần cộng cùng một kiểu synergy. Vì chưa có dữ liệu trận đấu theo rank Việt Nam, các điểm số không được hiệu chuẩn như mô hình dự đoán.

## Quy ước khắc chế và vai trò

`hero.counters` là danh sách **những tướng khắc chế hero**, không phải danh sách tướng mà hero khắc chế. Đảo chiều quan hệ này sẽ làm sai cả gợi ý và cảnh báo đối đầu.

`main_role` là lane ưu tiên; `roles` chứa mọi lane trong hồ sơ. Crawler lấy lane từ RoVGuide, không chuyển Fighter/Assassin/Mage thành lane. Patch Garena Việt Nam được lưu làm đối chiếu; ranked và lane chính của snapshot hiện tại theo máy chủ Thái. Người dùng có thể lọc và gợi ý tướng theo bất kỳ lane đã ghi nhận.

Các thuộc tính `damage`, `tankiness`, `mobility`, `teamfight`, `split_push` được `estimate_attributes` gán theo vai trò. Chúng không mô tả khác biệt kỹ năng của từng tướng trong cùng vai trò.

## Lưu trữ và phụ thuộc ngoài

Chỉ `theme` và `skipBanPhase` nằm trong `localStorage`. Không có lưu trận, đồng bộ đa thiết bị hoặc máy chủ nhiều người chơi. Ảnh tướng dùng URL nguồn; ảnh lỗi được thay bằng SVG sinh trong trình duyệt. Font được tải từ Google Fonts; biểu tượng giao diện là SVG nội tuyến, không cần thư viện icon ngoài. Giao diện gồm bảng hai đội theo chiều ngang, vùng tướng và cột gợi ý; dưới 880px, vùng tướng/gợi ý chuyển thành hai tab. Chi tiết lý do dùng phần tử `details`; bảng tổng kết hỗ trợ Escape và giữ focus bàn phím trong dialog.
