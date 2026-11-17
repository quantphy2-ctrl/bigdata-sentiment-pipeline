# W01 – Đặc tả Dashboard Batch + Streaming (bản nháp, Thành viên D)

> Trạng thái: **nháp W01**. Tên trường kết quả dựa trên đầu ra thống nhất trong kế hoạch (mục 04).
> Sẽ chốt lại khi A merge `docs/output_contract.md` (W02). Không dựng biểu đồ cảm xúc khi nhãn chưa tồn tại.

## 1. Câu hỏi Dashboard phải trả lời

| # | Câu hỏi | Biểu đồ |
|---|---|---|
| Q1 | Bao nhiêu bài/bình luận đã được xử lý (tổng, theo Batch/Stream)? | C1 |
| Q2 | Bao nhiêu positive / negative / neutral, tỷ lệ mỗi nhãn? | C2 |
| Q3 | Cảm xúc thay đổi thế nào theo thời gian? | C3 |
| Q4 | Nền tảng nào có tỷ lệ tiêu cực cao? | C4 |
| Q5 | Batch và Stream khác nhau thế nào (số lượng, phân bố nhãn, độ mới)? | C5 |
| Q6 | Sự kiện vừa gửi vào Kafka đã xuất hiện trên Kibana chưa? | C6 |
| Q7 | Pipeline stream có đang trễ không? | C7 |

## 2. Người xem

| Nhóm | Quan tâm | Dashboard dùng |
|---|---|---|
| Giảng viên | Bằng chứng 3V, so sánh Batch/Stream, demo "dữ liệu mới → biểu đồ đổi" | D2 |
| Nhóm trưởng (A) | Luồng còn sống, độ trễ, số document đúng | D1 |
| Thành viên trình bày ML (C) | Phân bố nhãn, độ tin cậy, model_version | D2 |

## 3. Hai dashboard tách biệt

| | **D1 – Pipeline Health (dùng ngay)** | **D2 – Sentiment Results (sau khi có ML)** |
|---|---|---|
| Data view | `social_events_v1` (time field `created_at`) | `sentiment_*_v1` (gồm `sentiment_batch_v1` + `sentiment_stream_v1`) |
| Có thể dựng | W01–W02 | Khi có document có `sentiment_label` (Batch W05, Stream W06) |
| Biểu đồ | C1 (không filter mode), C6, C7, đếm theo `kafka_partition` | C1–C5, C6 (có nhãn) |
| Mục đích | Kiểm tra dữ liệu thô đi qua Kafka → Spark → ES | Trả lời Q1–Q5 |

Dashboard v1 (`sentiment_data`) giữ nguyên để đối chiếu lịch sử; không phát triển thêm.

## 4. Danh mục biểu đồ

Quy ước: field có dấu `*` **chưa tồn tại** ở dữ liệu hiện tại.

### C1 – Tổng sự kiện đã xử lý (Metric)
- Câu hỏi: Q1. Loại: Lens Metric (Count), 2 ô cạnh nhau hoặc 1 ô + control filter.
- Field bắt buộc: `event_id`; `processing_mode*` để tách Batch/Stream.
- Data view: D1 → `social_events_v1`; D2 → `sentiment_*_v1`.
- Filter: `processing_mode : "batch"` / `"stream"`; tuỳ chọn `data_origin*`.
- Time field: `processed_at` (đếm theo thời điểm hệ thống xử lý – Batch có thể thiếu `created_at`).
- Nguồn: Spark Streaming v2 (hiện có), Batch ETL (B, W05).
- Kiểm tra: so với `GET <index>/_count` và số dòng đầu vào của Batch / số event Producer gửi.
- Hạn chế: Count trên Kibana phụ thuộc time range – phải đặt range bao trọn dữ liệu khi đối soát.

### C2 – Phân bố 3 nhãn cảm xúc (Bar chart, số lượng + %)
- Câu hỏi: Q2. Loại: Lens bar dọc, X = `sentiment_label*` (Top 3), Y = Count; bản thứ hai dùng "Percentage" (stacked 100%) hoặc formula `count() / overall_sum(count())`.
- Field: `sentiment_label*` (keyword: `positive|negative|neutral`).
- Data view: `sentiment_*_v1`. Filter: `processing_mode*`. Time field: `processed_at`.
- Màu cố định: positive xanh lá, neutral xám, negative đỏ (đặt trong Lens "color mapping" để Batch/Stream nhất quán).
- Kiểm tra: tổng 3 cột = C1; so với `terms` aggregation trên ES; so với confusion matrix/thống kê của C trên cùng tập.
- Hạn chế: Twitter Airline lệch về negative → tỷ lệ phản ánh dataset, không phải "dư luận chung".

### C3 – Diễn biến cảm xúc theo thời gian (Line / Area chart)
- Câu hỏi: Q3. Loại: Lens line, X = date histogram, breakdown = `sentiment_label*`.
- Chọn time field:
  - `created_at` khi muốn xem **khi nội dung xuất hiện** (ý nghĩa dư luận) – dùng cho Batch có timestamp gốc và Stream.
  - `collected_at` khi muốn xem **khi hệ thống nhận** (ý nghĩa vận hành, demo realtime).
  - Mặc định D2: `created_at`; thêm một bản `collected_at` cho demo.
- `created_at = null`: Kibana tự loại document khỏi date histogram theo field đó. Thêm Metric phụ "Số bản ghi không có created_at" (KQL `not created_at:*`) để không mất thông tin âm thầm.
- Hạn chế: Producer giả lập đặt `created_at = collected_at` → với dữ liệu demo, hai cách hiển thị giống nhau. Dữ liệu replay phải ghi rõ "replay".

### C4 – Cơ cấu cảm xúc theo nền tảng (Stacked bar 100%)
- Câu hỏi: Q4. Loại: Lens bar ngang stacked percentage, Y = `platform` (Top 10), breakdown = `sentiment_label*`.
- Field: `platform` (keyword – **không** dùng `platform.keyword` như dashboard v1), `sentiment_label*`.
- Data view: `sentiment_*_v1`. Filter: `processing_mode*`. Time field: `created_at`.
- Kiểm tra: kéo 1 platform sang Discover, đếm từng nhãn.
- Hạn chế: hiện chỉ có `simulated_reddit` (Stream) và dataset Batch sẽ có 1 nguồn chính → so sánh platform chỉ có nghĩa khi B bổ sung nguồn. Hiển thị số lượng tuyệt đối trong tooltip để tránh so 100% giữa nhóm 5 bản ghi với nhóm 10.000 bản ghi.

### C5 – So sánh Batch vs Stream
- Câu hỏi: Q5. Loại: (a) Lens bar nhóm X = `processing_mode*`, breakdown `sentiment_label*` (%); (b) bảng: `processing_mode*` | count | max(`processed_at`) | `model_version*`.
- Data view: `sentiment_*_v1` (yêu cầu mapping 2 index giống nhau – A chốt W02).
- Hạn chế: hai nhánh **không cùng nguồn dữ liệu** (Batch = dataset lịch sử, Stream = giả lập/replay) → chỉ so sánh phân bố và độ mới, **không** kết luận "Stream chính xác hơn Batch". Ghi chú này đặt ngay trên dashboard (Markdown panel).

### C6 – Sự kiện gần nhất (Saved search / bảng)
- Câu hỏi: Q6. Loại: Saved search trong Discover nhúng vào dashboard, sort `processed_at` desc, 20 dòng.
- Cột: `processed_at`, `event_id`, `platform`, `text`, `sentiment_label*`, `sentiment_confidence*`, `processing_mode*`.
- Data view: D1 `social_events_v1`; D2 `sentiment_stream_v1`. Auto-refresh dashboard 5–10 s khi demo.
- Kiểm tra: copy `event_id` từ log Producer, tìm trong bảng (đã làm ở smoke test ST-17/ST-21).

### C7 – Độ trễ pipeline (Metric + line)
- Câu hỏi: Q7. Loại: Lens Metric median / percentile 95 của runtime field `latency_s = (processed_at − collected_at)/1000`.
- Data view: `social_events_v1` / `sentiment_stream_v1` (runtime field khai báo trong data view, không đổi mapping).
- Hạn chế: chỉ đo đến lúc Spark bắt đầu ghi batch, độ phân giải 1 s; số liệu chính thức lấy từ bảng benchmark W08, không lấy từ dashboard.

## 5. Phụ thuộc chưa hoàn thành

| Phụ thuộc | Owner | Tuần | Ảnh hưởng |
|---|---|---|---|
| `docs/output_contract.md` + mapping `sentiment_*_v1` | A | W02 | Tên field C1–C7 |
| `processing_mode`, `data_origin`, `model_version` trong document | A, B | W05–W06 | C1, C5 |
| `sentiment_label`, `sentiment_confidence` | C (model), B/A (tích hợp) | W05 (Batch), W06 (Stream) | C2–C5 |
| Nguồn thứ hai / replay có platform khác | B | W04 | C4 có ý nghĩa |
| `processed_at` độ chính xác ms (đề xuất) | A | W03–W06 | C7 |

## 6. Bàn giao dự kiến
- `kibana/dashboards/D1_pipeline_health.ndjson` (W02), `kibana/dashboards/D2_sentiment_results.ndjson` (W07), export kèm data view.
