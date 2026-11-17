# W01 – Kiểm kê Elasticsearch & Kibana (Thành viên D)

- Người thực hiện: D – Đỗ Duy Đức
- Ngày: 17/11/2026 · Máy: máy D (Windows 11, UTC+7)
- Phiên bản repo: `main` @ `e3ba518` (đã gồm PR #4 Producer v2, PR #5 Spark v2, PR #6 README + script ES)
- Nhánh làm việc: `docs/w01-d-dashboard-qa`

## 1. Trường dữ liệu dùng cho lọc / tìm kiếm / dashboard

Nguồn: [`docs/data_schema.md`](../data_schema.md) (Schema v1.0) và mapping thực tế của `social_events_v1`
(lưu tại [`evidence/es_mapping_social_events_v1.json`](evidence/es_mapping_social_events_v1.json)).

| Trường | Kiểu ES thực tế | Dùng trong dashboard | Ghi chú |
|---|---|---|---|
| `event_id` | keyword | Tìm kiếm chính xác, đối soát, đếm trùng | Cũng là `_id` của document |
| `platform` | keyword | Terms/breakdown theo nguồn | Hiện chỉ có `simulated_reddit` |
| `content_type` | keyword | Filter post/comment | |
| `text` | text | Tìm full-text, bảng recent events | Không aggregate được (không có `.keyword`) |
| `language` | keyword | Filter | |
| `created_at` | date | Time field mặc định của data view | Có thể `null` với dữ liệu Batch |
| `collected_at` | date | Time field thay thế, tính latency | |
| `processed_at` | date | Tính latency, "lần cập nhật cuối" | Độ chính xác **giây**, gán **một lần cho cả micro-batch** |
| `engagement.likes/replies/shares` | long | Metric phụ | Producer gửi `null` – không điền 0 |
| `kafka_topic` | text + `.keyword` (map động) | Đối soát | Không khai báo trong script → dynamic mapping |
| `kafka_partition`, `kafka_offset` | long (map động) | Đối soát, kiểm trùng | |
| `sentiment_label` | keyword (đã khai báo) | Biểu đồ 3 nhãn | **Chưa có dữ liệu** – model chưa tích hợp |
| `sentiment_confidence` | float (đã khai báo) | Histogram độ tin cậy | **Chưa có dữ liệu** |
| `processing_mode` | keyword (đã khai báo) | Batch vs Stream | **Chưa có dữ liệu** |

Các trường còn thiếu so với output contract dự kiến (kế hoạch mục 04): `model_version`, `data_origin`.

## 2. Hai index theo kế hoạch

| Index | Pipeline | Trạng thái trên máy D (17/11) | Ghi chú |
|---|---|---|---|
| `sentiment_data` | v1 (`test_producer.py` → `spark_streaming.py`) | **Không tồn tại** (HTTP 404) | Môi trường sạch; chưa chạy v1. 9 mẫu v1 chỉ tồn tại trên máy A |
| `social_events_v1` | v2 (`test_producer_v2.py` → `spark_streaming_v2.py`) | Tạo bằng `scripts/create_es_index.ps1`; 12 document sau kiểm thử | Health **yellow** vì `number_of_replicas=1` trên ES single-node |
| `sentiment_batch_v1`, `sentiment_stream_v1` | Kết quả ML (kế hoạch) | Chưa có | Phụ thuộc `docs/output_contract.md` (A, W02) |

## 3. Saved Objects (.ndjson) ≠ dữ liệu Elasticsearch

- `kibana/group24-dashboard.ndjson` chỉ chứa **cấu hình** (index pattern, visualization, dashboard). Không chứa document.
- Import thành công **không** có nghĩa dashboard có dữ liệu: nếu index nguồn rỗng/không tồn tại, biểu đồ trống.
- Muốn tái tạo dữ liệu phải chạy lại pipeline (hoặc snapshot ES), không phải import .ndjson.

## 4. Danh mục đối tượng trong `group24-dashboard.ndjson`

| Loại | ID | Tiêu đề | Phụ thuộc |
|---|---|---|---|
| index-pattern | `3e4185a0-…95ce` | `sentiment_data` | Index `sentiment_data` (v1), **không có time field** |
| lens | `02fc3930-…95ce` | Total Social Media Comments (Metric, count) | index-pattern trên |
| lens | `6cd16c90-…95ce` | Comments by Platform (bar ngang, top 5 `platform.keyword`) | index-pattern trên |
| dashboard | `0ded2070-…95ce` | Big Data Sentiment Analysis - Group 24 | 2 lens trên |

Xuất từ Kibana **7.17.10** (khớp container). Kết quả import trên máy D: `successCount: 4`
([`evidence/kibana_import_result.json`](evidence/kibana_import_result.json)).

## 5. Giới hạn của Dashboard hiện tại

1. Dashboard v1 trỏ vào `sentiment_data` → trên máy mới **trống** cho tới khi chạy lại pipeline v1.
2. Lens "Comments by Platform" dùng `platform.keyword` (sinh ra từ dynamic mapping v1). Trên `social_events_v1`, `platform` đã là `keyword` và **không có** `.keyword` → **không thể tái sử dụng** visualization này bằng cách đổi data view; phải dựng lại.
3. Không có biểu đồ nào về cảm xúc, thời gian, Batch/Stream – vì dữ liệu tương ứng chưa tồn tại.
4. Data view `social_events_v1` chưa nằm trong file .ndjson của repo (mỗi máy phải tạo tay). Đề xuất: export lại sau W02 để vào repo.

## 6. Đối tượng cần khôi phục khi dựng máy mới

1. Index + mapping: `scripts/create_es_index.ps1` (v2). v1 chưa có script mapping.
2. Data view `sentiment_data` (trong .ndjson) và `social_events_v1` (time field `created_at`, tạo tay hoặc qua API).
3. Visualization + dashboard v1 (trong .ndjson).
4. Dữ liệu: chạy lại Producer + Spark (không nằm trong .ndjson).
