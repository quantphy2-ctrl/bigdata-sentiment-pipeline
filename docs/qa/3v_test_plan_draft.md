# Kế hoạch thực nghiệm 3V – bản nháp W01 (Thành viên D)

> Đây là **kế hoạch**: không có số liệu nào trong các bảng mẫu bên dưới. Số liệu thăm dò duy nhất hiện có nằm ở
> [`W01_smoke_test.md`](W01_smoke_test.md) §2 và không được dùng làm kết quả benchmark.

## 1. Định nghĩa

| V | Nghĩa trong dự án | Đo cái gì |
|---|---|---|
| **Volume** | Lượng dữ liệu hệ thống xử lý được | Số bản ghi, dung lượng, thời gian chạy, records/s của **Batch** |
| **Velocity** | Tốc độ và độ trễ xử lý dữ liệu đến liên tục | events/s, p50/p95 latency, backlog của **Stream** |
| **Variety** | Khả năng xử lý dữ liệu **khác cấu trúc, kiểu giá trị và mức thiếu trường** | Tỷ lệ map đúng schema, tỷ lệ lỗi parse, số trường mất thông tin |

## 2. Môi trường đo (phải ghi lại mỗi lần đo)

| Hạng mục | Máy D (17/11/2026) | Máy A | Cần A xác nhận |
|---|---|---|---|
| CPU | i5-12500H, 12C/16T | ? | |
| RAM | 15,6 GB (Docker VM ~7,6 GB) | ? | |
| Ổ đĩa | NVMe SSD 1 TB (WD SN560), C: còn trống ~365 GB | ? | |
| OS | Windows 11 Home | ? | |
| Docker / Compose | 29.9.3 / v5.7.0 | ? | |
| Spark | PySpark 3.5.1 `local[*]` (16 luồng logic) | ? | Số core thật dùng: `spark.sparkContext.defaultParallelism` |
| Java | Temurin 17.0.21 | ? | |
| Kafka | `social_events_v1`, 3 partition, RF 1 | | Số partition khi benchmark |
| ES | 7.17.10, 1 node, heap 1 GB | | Refresh interval |
| Spark worker container | Có chạy nhưng **không dùng** | | |

Quy tắc: tắt ứng dụng nặng khác; mỗi phép đo chạy **3 lần**, lần warm-up đầu (tải Maven/JIT) ghi riêng và **không** tính; báo cáo trung vị và min–max của 3 lần.

## 3. Volume (Batch)

**Mục tiêu:** chứng minh Batch xử lý được dữ liệu tăng dần và tìm điểm máy bắt đầu chậm/lỗi.

| Mục | Thiết kế |
|---|---|
| Bộ dữ liệu | Sentiment140 (1,6M dòng) cắt mẫu ngẫu nhiên có seed cố định; Twitter US Airline (~14,6k) làm mức nhỏ. B cung cấp manifest + checksum |
| Quy mô | 10.000 / 100.000 / 500.000 / 1.000.000 (dừng ở mức máy không đáp ứng, ghi rõ lý do) |
| Tác vụ (cố định cho mọi quy mô) | (1) đọc CSV → (2) validate + map schema v1.0 → (3) làm sạch text → (4) ghi Parquet → (5) suy luận model → (6) ghi ES `sentiment_batch_v1` |
| Đo từng pha | Ghi timestamp đầu/cuối mỗi pha trong log Batch (B thêm). Tối thiểu tách: *đọc+chuẩn hoá*, *ghi Parquet*, *inference*, *ghi ES* |
| Lưu ý Spark lazy | Pha đọc chỉ thực thi khi có action → đo theo action (`count()`/`write`) và ghi rõ phạm vi |
| Công cụ | Log Python (`time.perf_counter`), Spark UI (localhost:4040) cho stage time, `Get-Counter`/Task Manager cho CPU/RAM, `Get-ChildItem` cho dung lượng |
| Chỉ số | số dòng vào; hợp lệ; lỗi; dung lượng CSV vs Parquet; runtime; records/s; CPU/RAM đỉnh; error rate |
| Công thức | `throughput = records_processed / elapsed_seconds` (cùng phạm vi pha); `error_rate = records_invalid / records_input`; `compression = size_csv / size_parquet` |
| Đối soát | `records_valid + records_invalid = records_input`; `_count` ES = `records_valid` |
| Kết luận | Throughput ổn định hoặc giảm khi tăng quy mô; quy mô lớn nhất chạy được; không mất bản ghi |
| Giới hạn | 1 máy, `local[*]` – không chứng minh khả năng mở rộng cluster |

Bảng mẫu:

| dataset_size | records_valid | records_invalid | csv_mb | parquet_mb | phase | elapsed_s | records_s | cpu_peak / ram_peak | error_rate | trial | note |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 10000 | | | | | end-to-end | | | | | 1 | |

## 4. Velocity (Stream)

### 4.1 Các thời điểm

| Mốc | Trường | Hiện có? |
|---|---|---|
| T0 – Producer tạo sự kiện | `collected_at` | Có (độ chính xác giây) |
| T1 – Kafka nhận | Kafka record timestamp | Có trong Kafka, **chưa** đưa vào ES (đề xuất A thêm `kafka_timestamp`) |
| T2 – Spark bắt đầu ghi micro-batch | `processed_at` | Có (giây, chung cho cả batch) |
| T3 – Document tìm được trên ES | không có trường | Đo ngoài bằng công cụ poll |

- `processed_at − collected_at` = **T2 − T0**: bao gồm chờ Kafka + chờ trigger 5 s + lập lịch micro-batch; **không** gồm bulk write và refresh ES.
- End-to-end availability **T3 − T0**: script QA gửi sự kiện, ghi T0 (ms), poll `GET _doc/<event_id>` mỗi 100 ms, ghi T3 khi tìm thấy. Đây là chỉ số người dùng cảm nhận được.
- Đề xuất cho A: dùng timestamp **mili-giây** cho `collected_at`/`processed_at` khi benchmark (hiện giây → sai số tới ±1 s).

### 4.2 Kịch bản

| Kịch bản | Mô tả | Tham số đề xuất (A xác nhận) |
|---|---|---|
| Steady-state | Spark chạy sẵn; Producer phát đều | 10 / 50 / 100 / 500 events/s, mỗi mức 2–5 phút (≥ 1.000 sự kiện) |
| Backlog | Dừng Spark, đẩy N sự kiện vào Kafka, bật Spark | N = 10.000 / 100.000; đo thời gian xả hết backlog và records/s |
| Restart | Kill Spark giữa chừng, chạy lại cùng checkpoint | Đếm mất / trùng theo `event_id` |

Producer hiện chỉ gửi 3 câu cố định, không điều khiển được tốc độ → cần Producer có tham số `--rate`, `--count`, `--run-id` (A/B, W03–W06).

### 4.3 Chỉ số và cách tính

- `throughput = processed_n / (t_last_processed − t_first_sent)` (events/s).
- p50/p95: tính trên **toàn bộ** latency của các sự kiện hợp lệ trong một lần chạy, phương pháp nearest-rank (`numpy.percentile(..., method="nearest")` hoặc tương đương), sau đó báo trung vị của 3 lần chạy.
- Cỡ mẫu: p95 cần ≥ 100 sự kiện mỗi lần chạy (lý tưởng ≥ 1.000). **Không** suy p95 từ 3 sự kiện như đo sơ bộ W01.
- Mất dữ liệu: `lost = |sent_ids − es_ids|`; Trùng: `duplicates = es_docs_for_run − |unique es_ids|` (với `_id = event_id`, ES ghi đè nên còn phải kiểm `_version > 1` hoặc đếm số lần Spark log ghi cùng id).
- Tỷ lệ ghi ES thành công = `es_found / sent`.
- Backlog: Kafka consumer lag (`kafka-consumer-groups.sh --describe`) nếu lấy được; nếu không, ghi "không đo".

Công cụ: mở rộng [`scripts/qa/reconcile_events.py`](../../scripts/qa/reconcile_events.py) (đã có đối chiếu id + latency) để đọc danh sách id theo `run_id`.

Bảng mẫu:

| scenario | input_rate | n_events | processed_n | lost | duplicates | errors | p50_ms | p95_ms | throughput | trial | note |
|---|---|---|---|---|---|---|---|---|---|---|---|
| steady | 10/s | | | | | | | | | 1 | |

## 5. Variety

**Hai đầu vào tối thiểu** (phối hợp B):

| Nguồn | Định dạng | Khác biệt chính |
|---|---|---|
| Batch lịch sử | CSV (Twitter Airline / Sentiment140) | Tên cột khác (`airline_sentiment`, `tweet_created`, `target`…), timestamp kiểu chuỗi riêng/múi giờ khác, nhãn số (0/4) hoặc chữ, không có engagement |
| Stream | JSON lồng nhau (schema v1.0) | `engagement` là object, timestamp ISO UTC, thêm metadata Kafka |
| (Tuỳ chọn) Replay/API | JSON khác cấu trúc | Field thiếu / thừa |

Test cases (tối thiểu 6, mỗi case chạy trên cả CSV và JSON khi có nghĩa):

| ID | source_format | case | input | expected |
|---|---|---|---|---|
| V-01 | CSV, JSON | Text chứa emoji | `"Great flight 😍✈️"` | Giữ nguyên `text` gốc (UTF-8), map schema đúng; clean_text xử lý theo quy tắc của C |
| V-02 | CSV, JSON | URL + hashtag + mention | `"@united delay again #fail http://t.co/x"` | `text` gốc giữ nguyên; không lỗi parse |
| V-03 | CSV, JSON | Thiếu `created_at` | cột rỗng / field vắng | `created_at = null`, **không** tự điền thời gian hiện tại; vẫn vào pipeline; bị loại khỏi biểu đồ theo `created_at` (đếm ở metric riêng) |
| V-04 | JSON | Thiếu `engagement` hoặc `likes` | `{"engagement": {}}` | Các trường = `null`, **không** điền 0 |
| V-05 | CSV, JSON | Text rỗng / chỉ khoảng trắng | `""`, `"   "` | Bị đưa vào quarantine/invalid, có log lý do; không gửi model |
| V-06 | CSV | Tên cột / nhãn khác | Sentiment140 `target=0/4` vs Airline `airline_sentiment` | Adapter map đúng sang schema; nhãn gốc lưu riêng, không ghi đè `sentiment_label` của model |
| V-07 | CSV, JSON | Timestamp có múi giờ | `2015-02-24 11:35:52 -0800` | Chuyển đúng sang UTC `2015-02-24T19:35:52Z` |
| V-08 | JSON | JSON hỏng | `{"event_id": "x", "text": ` | Không làm chết stream; đếm là parse error (hiện Spark v2 lọc bỏ âm thầm – cần log) |
| V-09 | JSON | Thiếu `event_id` | không có field | Invalid, có log (hiện bị filter âm thầm) |
| V-10 | CSV | Dòng có dấu phẩy/xuống dòng trong text | text có `,` và `\n` trong ngoặc kép | Đọc đúng 1 bản ghi (`multiLine`, `escape`) |

Chỉ số: `schema_valid_rate = records_valid / records_input`; `parse_error_rate`; số trường bị mất/null hoá theo nguồn; số bản ghi quarantine; số bản ghi gán sai nguồn (`platform`/`data_origin`).

Bảng mẫu:

| source_format | case | input | expected | actual | pass_fail | note |
|---|---|---|---|---|---|---|
| CSV | V-03 | | | | | |

**Variety không chỉ là đếm số platform**: phải chứng minh hệ thống xử lý dữ liệu khác cấu trúc (CSV phẳng vs JSON lồng), khác kiểu (nhãn số vs chữ, timestamp có/không múi giờ) và khác mức độ thiếu trường, với kết quả đo được.

## 6. Lưu trữ kết quả

- File thô: `docs/qa/results/<V>_<scenario>_<yyyymmdd>_trial<k>.csv` + log gốc.
- Bảng tổng hợp + biểu đồ: `docs/qa/3v_results.md` (W08).
- Mọi số liệu phải trỏ được về file thô; không làm tròn trước khi tính percentile.
