# Dữ liệu và quy trình cập nhật

## Nguồn và phạm vi

| Nguồn | Nội dung | Giới hạn |
| --- | --- | --- |
| [AOV Builds: danh sách tướng](https://aov-builds.com/tuong/) | Danh sách tiếng Việt, slug, ảnh | Nguồn cộng đồng; ảnh vẫn nằm trên máy chủ nguồn |
| [AOV Builds: khắc chế](https://aov-builds.com/khac-che/) | Quan hệ khắc chế và giải thích theo từng tướng | Không phải tướng nào cũng có trang hoặc cấu trúc đọc được |
| [RovMeta](https://rovmeta.com/) | Tier, nhóm tướng, tỷ lệ, khắc chế dự phòng | Hướng đến máy chủ Thái; payload có thể chứa chỉ số thi đấu chuyên nghiệp |

Ngày thu thập không đồng nghĩa ngày phát hành bản cân bằng, ngày cập nhật nội dung nguồn hoặc ngày đo thống kê. `source_patch` phản ánh patch RovMeta công bố, không xác nhận patch máy chủ Việt Nam. Không dùng năm trong tiêu đề trang để suy ra độ mới của mọi trường dữ liệu.

## Snapshot ngày 21/10/2026

- 130 tướng; thêm Evita so với snapshot trước, không loại bỏ ID cũ.
- 129 tướng khớp RovMeta, patch nguồn `1.64`.
- 93 trang khắc chế chi tiết, 931 liên kết hợp lệ sau lọc và loại trùng.
- `flowbornphep` chưa có bản ghi meta riêng khớp chính xác; giữ chỉ số/tier cũ và đặt vai trò Mid theo ngoại lệ.
- Richter dùng bản ghi `Richter` khi nguồn không còn tên `Riktor`; Jinna khớp tên `Jinnar`.

Các số này mô tả lần cập nhật được lưu trong repository. Sau lần chạy mới, xem `data/data_update_report.json` để biết số liệu thực tế và sửa phần snapshot của README/tài liệu nếu cần.

## Schema tướng

`data/crawled_heroes.json` là mảng đối tượng; `HERO_DATABASE` trong `public/assets/js/app.js` phải giống hoàn toàn về nội dung.

| Trường | Kiểu / miền giá trị | Ý nghĩa |
| --- | --- | --- |
| `id` | Chuỗi chữ/số viết thường, duy nhất | Slug bỏ dấu, khoảng trắng và dấu câu |
| `name` | Chuỗi | Tên hiển thị tiếng Việt |
| `main_role` | `Top`, `Jungle`, `Mid`, `AD`, `SP` | Vai trò chính duy nhất |
| `tier` | `S+`, `S`, `A`, `B`, `C` | Tier nguồn hoặc dự phòng |
| `avatar` | Chuỗi URL | Ảnh tướng trên nguồn |
| `win_rate`, `pick_rate`, `ban_rate` | Số hữu hạn từ 0 đến 100 | Tỷ lệ %, có thể là dữ liệu cũ/mặc định nếu nguồn thiếu |
| `attributes` | Đối tượng 5 số nguyên 1–5 | `damage`, `tankiness`, `mobility`, `teamfight`, `split_push` |
| `counters` | Mảng `{id, reason}` | Những tướng khắc chế tướng đang xét |
| `tags` | Mảng chuỗi | Vai trò viết thường và nhãn `crawled` |

Ví dụ quan hệ: nếu Airi có `counters: [{"id": "ryoma", "reason": "..."}]`, hệ thống hiểu **Ryoma khắc chế Airi**. Counter ID phải tồn tại, không tự trỏ về chính tướng và không trùng trong cùng danh sách.

## Crawler hoạt động thế nào

1. Tải danh sách từ AOV Builds. Dừng nếu không tải được hoặc số lượng giảm xuống dưới 90% snapshot trước (tối thiểu 20).
2. Giải mã các chuỗi JSON trong Next.js stream của RovMeta; đọc `tiers`, giải tham chiếu `$…:tiers:…`, tạo bảng meta. Dừng nếu số bản ghi đọc được dưới 80% số tướng cũ (tối thiểu 20).
3. Ánh xạ tên bằng ID chuẩn hóa và bảng tên khác biệt. Không dùng khớp chuỗi con để đoán tướng.
4. Đọc trang khắc chế với tối đa 10 luồng; timeout danh sách/meta 15 giây, từng trang khắc chế 8 giây. Trang lỗi/không đọc được chuyển sang nguồn dự phòng; chưa có retry tự động.
5. Ưu tiên khắc chế AOV Builds, sau đó RovMeta, sau đó danh sách cũ nếu cả hai không có. Loại self-counter, ID không tồn tại và bản ghi trùng.
6. Lấy tỷ lệ/tier từ meta đã khớp; tỷ lệ thiếu giữ giá trị cũ hoặc mặc định WR=50, PR=5, BR=1. Tướng không khớp giữ tier cũ hoặc mặc định A, giữ vai trò cũ nếu có.
7. Áp dụng ngoại lệ vai trò; tạo thuộc tính ước lượng theo vai trò; kiểm tra schema trước khi ghi.
8. Ghi JSON, thay đúng một khối `HERO_DATABASE` trong JS, sau đó ghi báo cáo. Đường dẫn đầu ra được tính theo thư mục chứa crawler.

Việc ghi nhiều tệp chưa phải giao dịch nguyên tử. Nếu mất điện/lỗi ghi giữa chừng, chạy validator và đồng bộ lại hoặc khôi phục các tệp cùng một phiên bản bằng Git. Không sửa riêng JSON rồi mặc định ứng dụng đã nhận dữ liệu đó.

## Báo cáo cập nhật

`data/data_update_report.json` chứa:

- `fetched_at`: thời gian hoàn tất lấy dữ liệu, UTC theo ISO 8601.
- `sources`, `source_patch`: endpoint và patch của nguồn.
- `hero_count`, `meta_matches`, `detailed_counter_pages`, `counter_links`: độ phủ lần cập nhật.
- `unmatched_meta_ids`, `removed_ids`: tướng chưa khớp hoặc bị mất khỏi danh sách.
- `attributes_source`: nhắc rõ thuộc tính là ước lượng.
- `heroes[id].meta`: `rovmeta` hoặc `previous_or_default`.
- `heroes[id].stats_source`: nhãn nguồn trong payload (`pro`, `unspecified`, …); `unspecified` không xác nhận đó là thống kê rank.
- `heroes[id].fallback_rate_fields`: trường tỷ lệ dùng giá trị cũ/mặc định, không phải số mới lấy được từ nguồn.
- `heroes[id].counters`: `aov-builds`, `rovmeta`, `previous` hoặc `none`.

Báo cáo không lưu lịch sử nhiều lần chạy hoặc thời điểm xác minh ban đầu của giá trị cũ. Các trường dự phòng vì vậy vẫn được đánh dấu chưa xác minh độ mới. Giao diện hiện chưa hiển thị riêng nhãn nguồn cho từng chỉ số; đối chiếu báo cáo khi sử dụng hoặc công bố thống kê.

## Checklist sau cập nhật

```powershell
.\.venv\Scripts\python.exe scripts/crawler_system.py
.\.venv\Scripts\python.exe scripts/validate_data.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
node --check public/assets/js/app.js
git diff --stat
git diff -- scripts/crawler_system.py
```

Kiểm tra số lượng tướng, ID thêm/xóa, các trường fallback, phân bố vai trò và phần dữ liệu thay đổi trong diff. Mở ứng dụng, tìm tướng mới và thử chọn để xác nhận dữ liệu xuất hiện. Nếu nguồn thay HTML/Next.js hoặc đổi tên tướng, sửa parser/ánh xạ rồi chạy lại; không bỏ qua guard chỉ để có đầu ra.
