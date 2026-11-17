# W01 – Smoke test Producer → Kafka → Spark → Elasticsearch → Kibana (máy D)

## 0. Điều kiện chung

| Hạng mục | Giá trị |
|---|---|
| Người chạy | D – Đỗ Duy Đức (toàn bộ test chạy trên **máy D**, không dùng log máy A) |
| Ngày / giờ | 17/11/2026, 16:17–16:31 giờ máy (UTC+7) = 09:17–09:31 UTC |
| Múi giờ máy | `SE Asia Standard Time` (UTC+7). Dữ liệu JSON lưu **UTC**; Kibana hiển thị theo múi giờ trình duyệt (UTC+7) |
| Time filter Kibana khuyến nghị | `Last 24 hours` hoặc rộng hơn; time field `created_at` |
| Repo | `main` @ `e3ba518`, nhánh test `docs/w01-d-dashboard-qa` |
| CPU / RAM | Intel i5-12500H (12 nhân / 16 luồng), 15,6 GB RAM |
| Docker | Docker 29.9.3, Compose v5.7.0; Docker VM: 16 CPU, ~7,6 GB RAM |
| Python | 3.11.15 (cài qua `uv` – máy chỉ có sẵn 3.14), `.venv` trong repo |
| Thư viện | `pyspark==3.5.1`, `kafka-python` **3.0.13** (không pin trong `requirements.txt`) |
| Java | Máy có sẵn **JDK 25** (không tương thích) → dùng **Temurin 17.0.21** portable tại `%USERPROFILE%\tools\jdk-17.0.21+9`, chỉ set `JAVA_HOME` cho tiến trình Spark |
| Hadoop (Windows) | `winutils.exe` + `hadoop.dll` (Hadoop 3.3.5, nguồn `github.com/cdarlint/winutils`) tại `%USERPROFILE%\tools\hadoop\bin`; SHA256: winutils `A0CA6E35…44ADEA`, hadoop.dll `D3DD64AF…EE1C7B` |
| Spark mode | `local[*]` (container Spark Master/Worker chạy nhưng **không** được pipeline sử dụng) |

Bằng chứng nằm trong [`docs/qa/evidence/`](evidence/). Tên user Windows trong log đã được thay bằng `<user>`.

## 1. Bảng kiểm thử

| ID | Điều kiện trước | Thao tác / lệnh | Expected | Actual | Kết quả | Bằng chứng |
|---|---|---|---|---|---|---|
| ST-01 | Docker Desktop chạy | `docker compose -f .\docker\docker-compose.yml config --quiet` | Exit 0 | Exit 0 | PASS | – |
| ST-02 | ST-01 | `docker compose … up -d` rồi `ps` | 6 container Up | 6/6 Up: zookeeper, kafka, elasticsearch, kibana, spark-master, spark-worker | PASS | `docker_ps.txt` |
| ST-03 | ST-02 | `Invoke-RestMethod http://localhost:9200` | ES trả JSON | ES 7.17.10, cluster `docker-cluster` | PASS | – |
| ST-04 | Repo ở thư mục gốc | `Test-Path .\scripts\create_es_index.ps1` | `True` | `True` | PASS | – |
| ST-05 | ST-03, ST-04 | Đọc script rồi chạy `.\scripts\create_es_index.ps1` | Tạo index, 3 trường thời gian kiểu `date` | Tạo mới `social_events_v1`; `created_at/collected_at/processed_at = date` | PASS | `es_mapping_social_events_v1.json` |
| ST-06 | ST-05 | `GET _cat/indices` | Index healthy | `social_events_v1` **yellow** (`number_of_replicas=1` trên single-node) | PASS (cảnh báo) | Issue I-07 |
| ST-07 | Python 3.11 | Tạo `.venv`, `pip install -r requirements.txt`, import `pyspark`, `kafka` | PySpark 3.5.1, import OK | PySpark 3.5.1, kafka-python 3.0.13 | PASS | – |
| ST-08 | JDK mặc định của máy (25) | `python .\processing\spark_streaming_v2.py` | Spark khởi động | `UnsupportedOperationException: getSubject is not supported` → `JAVA_GATEWAY_EXITED` | **FAIL** | `spark_java25_stderr.log`, Issue I-01 |
| ST-09 | JDK 17, chưa có winutils | Như ST-08 | Spark khởi động | `HADOOP_HOME and hadoop.home.dir are unset` → SparkContext lỗi | **FAIL** | Issue I-02 (log ghi đè, xem mô tả) |
| ST-10 | JDK 17 + winutils, **topic chưa tồn tại** (môi trường sạch) | Chạy Spark trước Producer | Spark chờ dữ liệu | Spark khởi động, `UnknownTopicOrPartitionException` 3 lần rồi **thoát** | **FAIL** | `spark_v2_no_topic_stderr.log`, Issue I-03 |
| ST-11 | ST-05 | `GET social_events_v1/_count` | Ghi số ban đầu | `0` | PASS | – |
| ST-12 | ST-02 | Producer lượt 1: `python .\ingestion\test_producer_v2.py` (09:27:09Z) | Tạo topic 3 partition; 3 `event_id` khác nhau + partition/offset | "Da tao topic"; 3 id khác nhau, partition 1/2/2, offset 0/0/1 | PASS | `producer_run1.log`, `kafka_topic_describe.log` |
| ST-13 | Có 3 sự kiện backlog trong Kafka | Khởi động Spark (JDK 17 + winutils), sẵn sàng 09:27:41Z | Xử lý backlog, ghi ES | `Batch 0: da ghi 3 su kien`; count 0 → **3** | PASS | `spark_v2_session1_stdout.log` |
| ST-14 | Spark **đang chạy** | Producer lượt 2 (09:27:47Z) | +3 document | `Batch 1: 3 su kien`; count → **6** | PASS | `producer_run2.log` |
| ST-15 | Spark đang chạy | Producer lượt 3 (09:28:00Z) | +3 document | `Batch 2: 3 su kien`; count → **9** | PASS | `producer_run3.log` |
| ST-16 | ST-15 | `GET social_events_v1/_search` | Document có `event_id, platform, text, created_at, collected_at, processed_at, engagement` | Đủ trường + `content_type, language, kafka_topic, kafka_partition, kafka_offset` | PASS | `es_sample_doc.json` |
| ST-17 | ST-15 | `scripts/qa/reconcile_events.py` đối chiếu từng `event_id` Producer ↔ ES | Không thiếu id; partition/offset khớp | 12/12 id có trong ES, partition/offset khớp, 0 thiếu | PASS | `reconcile_result.txt` |
| ST-18 | ST-17 | So sánh `_id` với `event_id` | `_id == event_id` | `True` cho 12/12 | PASS | `reconcile_result.txt` |
| ST-19 | Spark bị dừng (kill tiến trình), checkpoint giữ nguyên | Chạy lại Spark, chờ ~20 s, rồi Producer lượt 4 | Không xử lý lại sự kiện cũ; sự kiện mới vào | Count giữ **9** khi idle; Spark tiếp tục từ `Batch 3`; count → **12** | PASS | `spark_v2_session2_restart_stdout.log`, `producer_run4_after_restart.log` |
| ST-20 | Kibana green | Tạo data view `social_events_v1`, time field `created_at` (qua Saved Objects API) | Tạo được | Tạo thành công, id `social_events_v1` | PASS | `kibana_dataview_create.json` |
| ST-21 | ST-20 | Discover: tìm `event_id : "demo_3c001093624d45e3b4d487b62ef0509d"`, time range Last 24h | Thấy 1 sự kiện | Truy vấn `term` tương đương trên ES trả 1 hit; **chưa chụp ảnh Discover** | PENDING (cần thao tác tay) | Xem §3 |
| ST-22 | Kibana 7.17.10 | Import `kibana/group24-dashboard.ndjson` | Import 4 object | `successCount: 4` | PASS | `kibana_import_result.json` |
| ST-23 | ST-22 | Mở dashboard "Big Data Sentiment Analysis - Group 24" | 2 biểu đồ hiển thị | Import được nhưng index `sentiment_data` **không tồn tại** (404) → biểu đồ không có dữ liệu | PASS (import) / NO DATA | Issue I-08 |
| ST-24 | Spark chạy nền | Dừng Spark | Dừng có kiểm soát | Dừng bằng kill tiến trình (chạy nền, không gửi được Ctrl+C); checkpoint vẫn dùng được (ST-19) | PASS (ghi chú) | – |

**Tổng:** 19 PASS · 3 FAIL (đều là môi trường, đã có cách khắc phục) · 1 PENDING thao tác tay · 1 NO DATA (dự kiến).

## 2. Số liệu độ trễ thăm dò (KHÔNG phải benchmark)

`latency = processed_at − collected_at`, độ chính xác **1 giây**; `processed_at` gán một lần cho cả micro-batch.

| Kịch bản | Lượt | n | Latency (s) | Ghi chú |
|---|---|---|---|---|
| Backlog | 1 | 3 | 26 / 26 / 26 | Gồm ~31 s chờ Spark khởi động sau khi Producer gửi; đo thời gian chờ, không đo tốc độ xử lý |
| Steady-state | 2 | 3 | 2 / 2 / 2 | Trigger 5 s |
| Steady-state | 3 | 3 | 4 / 4 / 4 | |
| Sau restart | 4 | 3 | 6 / 6 / 6 | Spark mới khởi động lại ~20 s trước |

Steady-state (lượt 2–3): n = 6, trung vị 3 s. Với n nhỏ và độ phân giải giây, **không** dùng để kết luận p95.
Không chỉ số nào ở đây đo thời điểm document *có thể tìm thấy* trên ES (sau refresh).

## 3. Việc còn thiếu – cần D làm tay trên trình duyệt

- [ ] Ảnh Kibana Discover (`social_events_v1`, Last 24 hours) tìm thấy `demo_3c001093624d45e3b4d487b62ef0509d` → lưu `docs/qa/evidence/kibana_discover.png`, đổi ST-21 thành PASS.
- [ ] Ảnh dashboard v1 sau import (trống dữ liệu) → `docs/qa/evidence/kibana_dashboard_v1.png`.
- [ ] (Tuỳ chọn) Ảnh `docker compose ps` và terminal Producer/Spark nếu giảng viên yêu cầu ảnh thay vì file log.

## 4. Cách chạy lại trên máy D

```powershell
# Terminal Spark (chỉ áp dụng cho tiến trình này)
$env:JAVA_HOME  = "$env:USERPROFILE\tools\jdk-17.0.21+9"
$env:HADOOP_HOME = "$env:USERPROFILE\tools\hadoop"
$env:PATH = "$env:JAVA_HOME\bin;$env:HADOOP_HOME\bin;$env:PATH"
.\.venv\Scripts\python.exe .\processing\spark_streaming_v2.py

# Trên môi trường sạch: chạy Producer TRƯỚC một lần để tạo topic (xem I-03)
.\.venv\Scripts\python.exe .\ingestion\test_producer_v2.py

# Đối soát
.\.venv\Scripts\python.exe .\scripts\qa\reconcile_events.py "docs/qa/evidence/producer_run*.log"
```
