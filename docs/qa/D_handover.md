# D – Bàn giao Tuần 01 (Đỗ Duy Đức – Dashboard / QA / Benchmark)

Nhánh: `docs/w01-d-dashboard-qa` · Base: `main` @ `e3ba518` · Ngày: 17/11/2026

## 1. Sản phẩm

| Sản phẩm | File | Trạng thái |
|---|---|---|
| Kiểm kê ES/Kibana, .ndjson, hai index, giới hạn dashboard | [`docs/qa/W01_kibana_inventory.md`](W01_kibana_inventory.md) | Xong |
| Smoke test trên máy D (24 bước, expected/actual, bằng chứng) | [`docs/qa/W01_smoke_test.md`](W01_smoke_test.md) | Xong, còn 1 ảnh Discover chụp tay |
| Bằng chứng (log Producer/Spark, mapping, kết quả đối soát, import Kibana) | [`docs/qa/evidence/`](evidence/) | Xong |
| Script đối soát `event_id` Producer ↔ ES + latency | [`scripts/qa/reconcile_events.py`](../../scripts/qa/reconcile_events.py) | Xong (chỉ đọc ES) |
| Đặc tả Dashboard Batch + Stream + 3 nhãn | [`docs/dashboard/W01_dashboard_spec.md`](../dashboard/W01_dashboard_spec.md) | Nháp, chờ output contract |
| Kế hoạch thực nghiệm 3V | [`docs/qa/3v_test_plan_draft.md`](3v_test_plan_draft.md) | Nháp, chờ A xác nhận tham số |
| Ghi chú phương pháp + phương án thay thế | [`docs/methods/D_dashboard_qa_methods.md`](../methods/D_dashboard_qa_methods.md) | Sơ bộ |

## 2. Kết quả chính

- Pipeline v2 **chạy được trên máy D** sau khi xử lý 2 vấn đề môi trường (JDK 17, winutils).
- 4 lượt Producer × 3 sự kiện = 12 sự kiện; **12/12 `event_id` có trong ES**, partition/offset khớp, `_id = event_id`.
- Spark xử lý cả backlog (Batch 0) và sự kiện mới khi đang chạy (Batch 1, 2).
- Restart cùng checkpoint: không xử lý lại sự kiện cũ, tiếp tục từ Batch 3.
- Import `group24-dashboard.ndjson` thành công (4 object) nhưng **không có dữ liệu** vì index `sentiment_data` không tồn tại trên máy mới.
- Latency thăm dò steady-state 2–4 s (n=6, độ phân giải 1 s) – **không phải benchmark**.

## 3. Issues / Blockers

| ID | Mức | Mô tả | Đề xuất | Owner đề xuất |
|---|---|---|---|---|
| I-01 | Cao | Máy có JDK 25 → Spark 3.5.1 lỗi `getSubject is not supported`. README ghi "JDK 17" nhưng không có bước kiểm tra/hướng dẫn khi có Java khác | README: thêm cảnh báo Java ≥ 18 không chạy, hướng dẫn Temurin 17 portable + set `JAVA_HOME` theo terminal | A |
| I-02 | Cao | Spark trên Windows bắt buộc `winutils.exe`/`hadoop.dll`; README không có bước này, chỉ nhắc `setup_hadoop.py` kèm "lưu ý bảo mật phía dưới" nhưng **không có** mục đó. `spark_streaming_v2.py` hardcode `C:\hadoop` | README: bước cài HADOOP_HOME, nêu nguồn + checksum; script đọc `HADOOP_HOME` từ env trước khi dùng `C:\hadoop` | A |
| I-03 | Trung bình | Môi trường sạch: chạy Spark trước Producer → `UnknownTopicOrPartitionException`, query thoát sau 3 lần thử. Kế hoạch W01 yêu cầu "Spark trước Producer" | Tách bước tạo topic (script `scripts/create_kafka_topic.*` hoặc `kafka-topics.sh` trong README) chạy trước Spark | A |
| I-04 | Thấp | README bắt đầu từ mục 3; mục 1–2 ("Trạng thái dự án") bị mất, anchor `#2-trạng-thái-dự-án` hỏng | Bổ sung lại mục 1–2 | A |
| I-05 | Trung bình | `requirements.txt` không pin `kafka-python` (máy D cài 3.0.13) | Pin phiên bản đã thử trên máy A | A |
| I-06 | Trung bình | `zookeeper:latest`, `wurstmeister/kafka:latest` không pin; Spark container 3.3.0 ≠ PySpark 3.5.1 local | Pin tag image; ghi rõ container Spark chưa dùng / đồng bộ phiên bản nếu dùng cluster | A |
| I-07 | Thấp | `social_events_v1` health **yellow** (`number_of_replicas=1` trên 1 node) | Thêm `"settings": {"number_of_replicas": 0}` vào `create_es_index.ps1` cho các index mới | A |
| I-08 | Trung bình | Dashboard v1 phụ thuộc index `sentiment_data` + field `platform.keyword` → trống trên máy mới, không tái sử dụng được cho v2 | Giữ làm tham chiếu; D dựng D1 mới trên `social_events_v1` (W02) | D |
| I-09 | Trung bình | `processed_at` độ chính xác giây, gán chung cho cả micro-batch → không đủ cho p50/p95 W08 | Dùng ms (`isoformat(timespec="milliseconds")`) cho `collected_at`/`processed_at`; thêm `kafka_timestamp` | A (Stream), B (Producer/replay) |
| I-10 | Trung bình | Spark v2 lọc bỏ âm thầm JSON hỏng / thiếu `event_id` → không đo được tỷ lệ invalid (W03) | Đếm & log số bản ghi bị loại mỗi batch (hoặc ghi quarantine) | A |
| I-11 | Thấp | Producer chỉ gửi 3 câu cố định, không có `--rate/--count` → chưa benchmark Velocity được | Producer/replay có tham số tốc độ, số lượng, `run_id` | A/B |
| I-12 | Thấp | Mapping chưa khai báo `kafka_*` (map động: `kafka_topic` thành text+keyword); chưa có `model_version`, `data_origin` | Chốt trong `output_contract.md` | A |

## 4. Cấu hình riêng trên máy D (không commit)

- `.venv` (Python 3.11.15 qua `uv`), Temurin JDK 17 tại `%USERPROFILE%\tools\jdk-17.0.21+9`, winutils tại `%USERPROFILE%\tools\hadoop\bin`.
- `checkpoints/social_events_v1` (đã nằm trong `.gitignore`).
- Kibana máy D: đã import dashboard v1 và tạo data view `social_events_v1` (time field `created_at`).

## 5. Việc tiếp theo của D (W02)

- [ ] Chụp ảnh Discover + dashboard v1 (xem smoke test §3).
- [ ] Nhận phản hồi A về I-01…I-12; cập nhật trạng thái.
- [ ] Chốt dashboard/QA theo `output_contract.md`; dựng D1 Pipeline Health, export `.ndjson`.
- [ ] Thống nhất với A tham số Velocity (rate, partition), với B danh sách nguồn cho Variety.

## 6. Phản hồi từ A

> _(A điền khi review PR)_
