# Kiến trúc và thuật toán

## Thành phần và luồng dữ liệu

```text
AOV Builds ── danh sách, ảnh, khắc chế ──┐
                                        ├── scripts/crawler_system.py
RovMeta ──── tier, chỉ số, khắc chế ─────┘          │
                                                  ├── data/crawled_heroes.json
                                                  ├── public/assets/js/app.js
                                                  └── data/data_update_report.json

public/ ── máy chủ tĩnh ── trình duyệt ── thao tác draft và gợi ý
```

Không có API backend hoặc database server. Frontend đọc hằng `HERO_DATABASE` nhúng trong `public/assets/js/app.js`; tệp JSON phục vụ kiểm tra và bảo trì, không được frontend `fetch` lúc chạy. Muốn thay dữ liệu hiển thị phải đồng bộ cả hai bản rồi tải lại trang.

## Trạng thái và lượt chơi

`TURN_SEQUENCE` gồm 20 bước: 10 bước cấm xen kẽ Xanh/Đỏ, sau đó 10 bước chọn theo thứ tự đội Xanh, Đỏ, Đỏ, Xanh, Xanh, Đỏ, Đỏ, Xanh, Xanh, Đỏ. Đây là quy tắc mô phỏng của ứng dụng, không phải cam kết cập nhật mọi chế độ thi đấu hiện hành.

`state` chứa chỉ số lượt, bốn mảng cấm/chọn, bộ lọc, kiểu sắp xếp, chế độ gợi ý và lịch sử. Mỗi mảng đội có 5 vị trí. `handleHeroSelect` ghi snapshot lịch sử trước khi đổi trạng thái; `handleUndo` khôi phục snapshot, `handleReset` tạo lại lượt đầu theo tùy chọn bỏ qua cấm.

Khi khởi động, `DOMContentLoaded` gắn sự kiện, nạp theme/tùy chọn cấm và gọi `renderUI`. Các hàm `renderHeroGrid`, `renderRecommendationsAndStats`, `renderCompositionStats` cập nhật DOM. Tướng đã cấm/chọn bị loại khỏi tập gợi ý và vô hiệu hóa trên lưới.

## Tính điểm gợi ý

`calculateSuggestions(teamType)` lấy đội nhà/đối phương, vai trò còn thiếu và các chỉ số tổng hợp; lọc tướng chưa dùng theo bộ lọc gợi ý, chấm điểm rồi trả về tối đa 6 tướng có điểm cao nhất.

| Thành phần | Chế độ Meta | Chế độ Khắc chế |
| --- | --- | --- |
| Điểm tier S+/S/A/B/C | 55 / 50 / 40 / 30 / 20 | 22 / 21 / 20 / 19 / 18 |
| Điều chỉnh chỉ số | `round((WR−50)×0.1 + (PR−10)×0.6 + (BR−5)×0.3)` | `round((WR−50)×0.02 + (PR−10)×0.1 + (BR−5)×0.05)` |

WR/PR/BR là tỷ lệ theo phần trăm, ví dụ `52.5`, không phải `0.525`.

Các quy tắc bổ sung áp dụng trong cả hai chế độ:

- Khắc chế một tướng địch: +20; ưu tiên `COUNTERS_MANUAL`, sau đó tra `enemy.counters`.
- Bị tướng địch khắc chế trong dữ liệu crawler: −15.
- Cướp tướng khắc chế đồng đội khi địch chưa có vai trò tương ứng: +15.
- Hiệp lực giao tranh khi cả đồng đội và ứng viên có `teamfight >= 4`: +10.
- Bù chống chịu, giao tranh, sát thương hoặc cơ động còn thiếu: mỗi điều kiện +15.
- Một số tình huống khắc chế loại đội hình/cơ động/sốc sát thương: +15.
- Bổ sung vai trò, tuyến trước, Mid hoặc AD: một số điều kiện +1, không hiện trong phần lý do.

Các điều kiện có thể cộng dồn; điểm không bị giới hạn trong thang 0–100. Một số điểm nhỏ không có lý do hiển thị, nên cộng các lý do chưa chắc bằng tổng điểm. Đánh giá sức mạnh đội hình dựa trên trung bình thuộc tính 1–5, không phải mô hình dự báo kết quả trận đấu.

## Quy ước khắc chế và vai trò

`hero.counters` là danh sách **những tướng khắc chế hero**, không phải danh sách tướng mà hero khắc chế. Đảo chiều quan hệ này sẽ làm sai cả gợi ý và cảnh báo đối đầu.

Mỗi tướng chỉ có một `main_role`. Crawler chuyển nhóm tướng từ RovMeta thành vai trò đường, rồi áp dụng `ROLE_OVERRIED` cho một số ngoại lệ. Đây là phép gần đúng; chưa có mô hình đa vai trò hoặc kiểm tra bắt buộc đủ 5 đường khi người dùng chọn.

Các thuộc tính `damage`, `tankiness`, `mobility`, `teamfight`, `split_push` được `estimate_attributes` gán theo vai trò. Chúng không mô tả khác biệt kỹ năng của từng tướng trong cùng vai trò.

## Lưu trữ và phụ thuộc ngoài

Chỉ `theme` và `skipBanPhase` nằm trong `localStorage`. Không có lưu trận, đồng bộ đa thiết bị hoặc máy chủ nhiều người chơi. Ảnh tướng dùng URL nguồn; ảnh lỗi được thay bằng SVG sinh trong trình duyệt. Font và bộ icon được tải từ Google Fonts/CDN, nên cần tính đến kết nối mạng khi triển khai.
