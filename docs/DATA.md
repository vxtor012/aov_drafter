# Dữ liệu và quy trình cập nhật

## Nguồn và phạm vi

| Nguồn | Dùng cho | Phạm vi và giới hạn |
| --- | --- | --- |
| [RoVGuide — Ranked Meta](https://rovguide.com/meta) | Tier, tỷ lệ thắng/chọn/cấm của chế độ Meta | Ranked máy chủ Thái Lan; trang công bố ngày chốt riêng. Không đại diện cho người chơi Việt Nam. |
| [RoVGuide — hồ sơ tướng](https://rovguide.com/heroes) | Lane chính và lane phụ | Hồ sơ game ở hệ RoV Thái; không phải thống kê lane của máy chủ Việt. Crawler đối chiếu đủ roster trước khi ghi. |
| [RovMeta](https://rovmeta.com/) | Nguồn khắc chế dự phòng và đối chiếu chuyên nghiệp | Dữ liệu chuyên nghiệp có thể khác ranked và có ít tướng hơn; không còn dùng lớp tướng của nguồn này để suy ra lane. |
| [AOV Builds](https://aov-builds.com/tuong/) | Roster, tên/ảnh và quan hệ khắc chế cộng đồng | Nội dung hướng đến người chơi Việt, nhưng bài viết/tư vấn có thể thay đổi không đồng bộ theo patch. |
| [Garena Việt Nam — cập nhật 08/04/2026](https://lienquan.garena.vn/chi-tiet-ban-cap-nhat-le-hoi-5v5-08-04-2026/) | Đối chiếu thay đổi lane/balance của bản VN | Lưu làm nguồn tham chiếu; không ghi đè meta và lane Thái trong snapshot hiện tại. |

RoVGuide công bố ngày chốt ranked và tách ranked khỏi thi đấu chuyên nghiệp; ứng dụng dùng ranked làm tín hiệu gần với nhu cầu draft của người chơi hơn. Vùng máy chủ và ngày snapshot được lưu theo tướng, đồng thời hiện trong chế độ Meta. Các nguồn Thái được ưu tiên vì độ cập nhật; nên đọc điểm gợi ý như tham khảo cho meta Thái, không phải dự báo chính xác kết quả ở Việt Nam.

## Snapshot ngày 21/10/2026

- 130 tướng, tất cả khớp dòng ranked RoVGuide; dữ liệu ranked chốt ngày `2026-10-19`.
- 130 hồ sơ lane; 30 tướng có nhiều hơn một lane.
- Tier nguồn RoVGuide `T0`–`T4` được đổi lần lượt thành `S+`, `S`, `A`, `B`, `C` để giữ tương thích giao diện.
- 93 trang khắc chế chi tiết từ AOV Builds, 931 liên kết sau lọc và loại trùng.
- Astrid có lane chính `Jungle`, lane phụ `Top` theo hồ sơ Thái; Garena VN cũng từng ghi nhận chuyển vị trí chính từ Caesar sang Rừng trong bản 08/04/2026.
- Thống kê ranked không dùng giá trị cũ/mặc định. Nếu nguồn ranked hoặc hồ sơ lane thiếu, crawler dừng trước khi ghi snapshot.

Đây là số liệu của lần cập nhật đã lưu. Sau khi chạy crawler, đối chiếu `data/data_update_report.json` và cập nhật snapshot này nếu số liệu thay đổi.

## Schema tướng

`data/crawled_heroes.json` là mảng bản ghi; `HERO_DATABASE` trong `public/assets/js/app.js` phải đồng bộ hoàn toàn.

| Trường | Kiểu / miền giá trị | Ý nghĩa |
| --- | --- | --- |
| `id` | Chuỗi chữ/số viết thường, duy nhất | ID ổn định từ roster AOV Builds |
| `name` | Chuỗi | Tên hiển thị tiếng Việt |
| `main_role` | `Top`, `Jungle`, `Mid`, `AD`, `SP` | Lane ưu tiên đầu tiên trong `roles` |
| `roles` | Mảng lane không trùng | Các lane trong hồ sơ nguồn, theo thứ tự ưu tiên |
| `tier` | `S+`, `S`, `A`, `B`, `C` | Tier chuyển đổi từ ranked RoVGuide |
| `win_rate`, `pick_rate`, `ban_rate` | Số hữu hạn 0–100 | Phần trăm ranked Thái Lan tại `meta_snapshot` |
| `meta_source`, `meta_snapshot` | Chuỗi | Nguồn thống kê và ngày chốt snapshot |
| `roles_source`, `roles_region` | Chuỗi | URL hồ sơ lane và vùng nguồn (`TH`) |
| `roles_cross_check` | URL hoặc `null` | Patch VN liên quan nếu có dùng để đối chiếu |
| `avatar` | URL | Ảnh tướng trên nguồn |
| `attributes` | Đối tượng 5 số nguyên 1–5 | Ước lượng theo lane cho phần phân tích đội hình; không dùng trong điểm gợi ý |
| `counters` | Mảng `{id, reason}` | Những tướng được nguồn ghi là khắc chế tướng đang xét |
| `tags` | Mảng chuỗi | Lane viết thường và nhãn `crawled` |

Ví dụ quan hệ: nếu Airi có `counters: [{"id":"ryoma","reason":"..."}]`, ứng dụng hiểu **Ryoma khắc chế Airi**. ID phải tồn tại, không tự trỏ về chính tướng và không lặp.

## Crawler

1. Tải roster, tên và ảnh từ AOV Builds. Dừng nếu danh sách giảm bất thường so với snapshot trước.
2. Đọc tier và counter dự phòng từ payload RovMeta. Nhóm `fighter`, `mage`, `assassin`… là lớp tướng, tuyệt đối không chuyển trực tiếp thành lane.
3. Đọc bảng ranked RoVGuide và ngày snapshot; ánh xạ đủ từng ID với slug nguồn. Crawler yêu cầu ít nhất 90% bảng đọc được và phải khớp mọi tướng trước khi ghi.
4. Đọc hồ sơ lane của từng tướng bằng 10 luồng. Chỉ ghi khi mọi trang khớp được và có lane hợp lệ; không dùng lớp tướng hay giá trị cũ để đoán lane.
5. Ưu tiên counter AOV Builds, sau đó counter RovMeta, sau đó dữ liệu cũ nếu hai nguồn đều thiếu. Loại self-counter, ID không tồn tại và bản ghi lặp.
6. Gán tier/tỷ lệ từ ranked Thái Lan, `main_role` bằng lane đầu tiên và `roles` bằng toàn bộ lane trong hồ sơ. URL Garena VN được lưu để kiểm tra chéo, không thay nguồn lane Thái.
7. Tạo thuộc tính phân tích theo lane, kiểm tra schema và chỉ sau đó ghi JSON, đồng bộ khối JavaScript và báo cáo.

Lần chạy hoàn tất hiện dùng 10 luồng cho counter và 10 luồng cho hồ sơ lane. Lỗi nguồn, ngày snapshot không đọc được, alias chưa biết hoặc thiếu tướng sẽ làm crawler dừng trước khi cập nhật tệp. Việc ghi ba tệp chưa phải một giao dịch nguyên tử; nếu xảy ra lỗi ghi, chạy validator và khôi phục hoặc đồng bộ các tệp từ cùng một snapshot Git.

## Báo cáo cập nhật

`data/data_update_report.json` lưu:

- `fetched_at`, `ranked_snapshot`, `ranked_region`, `rovmeta_reference_patch`: thời điểm lấy, ngày chốt ranked, vùng máy chủ và patch RovMeta dùng làm nguồn đối chiếu.
- `hero_count`, `rovmeta_reference_matches`, `detailed_counter_pages`, `counter_links`: độ phủ roster, đối chiếu RovMeta và counter.
- `sources`: URL của roster, hồ sơ lane, ranked, counter và nguồn đối chiếu.
- `heroes[id].stats_source`, `stats_snapshot`, `rovmeta_reference`: nguồn ranked cho từng bản ghi và tình trạng đối chiếu RovMeta.
- `heroes[id].roles_source`, `roles_source_region`, `roles_cross_check`: nguồn lane và URL đối chiếu VN nếu có.
- `heroes[id].counters`: `aov-builds`, `rovmeta`, `previous` hoặc `none`.
- `fallback_rate_fields`: trường thống kê dùng dự phòng; snapshot hiện tại cần danh sách rỗng.

## Đồng bộ và kiểm tra

```powershell
.\.venv\Scripts\python.exe scripts/crawler_system.py
.\.venv\Scripts\python.exe scripts/validate_data.py
node --check public/assets/js/app.js
git diff --check
```

Xem phân bố lane chính, số lane phụ, tướng thêm/xóa, ngày snapshot, nguồn counter và JSON diff trước khi triển khai. Trình duyệt không tự tải dữ liệu từ Internet.
