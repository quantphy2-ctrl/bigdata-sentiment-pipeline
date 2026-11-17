# Ghi chú phương pháp – D (Dashboard / QA / Benchmark) – bản sơ bộ W01

Mục đích: giải trình **vì sao** chọn cách làm, kèm ít nhất một phương án thay thế cho mỗi lựa chọn quan trọng.

## 1. Kiểm thử luồng: đối chiếu theo `event_id` thay vì chỉ đếm `_count`

- **Chọn:** đối chiếu từng `event_id` Producer in ra với document ES (`GET _doc/<id>`), kèm partition/offset.
- **Lý do:** `_count` có thể đúng "do trùng hợp" (sự kiện cũ được ghi lại, sự kiện mới bị mất). Đối chiếu id phát hiện được cả mất lẫn sai nguồn. Trên máy D: 12/12 id khớp, partition/offset khớp.
- **Thay thế:** chỉ so `_count` trước/sau – nhanh, đủ cho demo, nhưng không phát hiện mất+trùng bù trừ nhau. Dùng làm kiểm tra nhanh, không dùng làm bằng chứng.

## 2. Chạy Spark trước Producer (steady-state) và tách backlog

- **Chọn:** đo riêng hai kịch bản; chỉ steady-state phản ánh độ trễ xử lý.
- **Lý do:** kết quả W01 cho thấy backlog cho latency 26 s (thực chất là thời gian chờ Spark khởi động), steady-state 2–4 s. Gộp hai loại làm p95 vô nghĩa.
- **Phát hiện:** trên môi trường sạch, Spark chết nếu topic chưa tồn tại → phải tạo topic trước (Issue I-03).
- **Thay thế:** chỉ đo backlog (đổ sẵn N sự kiện) – dễ tái lập, đo được throughput tối đa, nhưng không đo độ trễ người dùng cảm nhận. Dùng bổ sung cho Volume-trong-Stream.

## 3. Hai dashboard: Pipeline Health vs Sentiment Results

- **Chọn:** D1 dùng ngay trên `social_events_v1`; D2 chỉ dựng khi `sentiment_label` có thật.
- **Lý do:** tránh trình bày biểu đồ cảm xúc rỗng hoặc dữ liệu giả; tách người xem kỹ thuật (A) với người xem kết quả (giảng viên).
- **Thay thế:** một dashboard duy nhất với control filter `processing_mode` – gọn hơn khi demo, nhưng trộn chỉ số vận hành với chỉ số phân tích. Có thể gộp ở W07 nếu giảng viên muốn một màn hình.

## 4. Hai index kết quả + pattern `sentiment_*_v1`

- **Chọn:** theo kế hoạch – `sentiment_batch_v1`, `sentiment_stream_v1`, mapping giống nhau, Kibana đọc qua wildcard.
- **Lý do:** không ghi đè dữ liệu raw `social_events_v1`; mỗi nhánh xoá/chạy lại độc lập; so sánh bằng `processing_mode`.
- **Thay thế:** một index `sentiment_v1` duy nhất phân biệt bằng `processing_mode` – truy vấn đơn giản hơn, nhưng chạy lại Batch phải `delete_by_query`, dễ đụng dữ liệu Stream.
- **Điều kiện:** mapping hai index phải khớp tuyệt đối (một field khác kiểu → Kibana báo conflict trên data view wildcard). D sẽ kiểm bằng `GET sentiment_*_v1/_mapping` sau W02.

## 5. Chọn loại biểu đồ

| Dữ liệu | Chọn | Thay thế | Vì sao không chọn thay thế |
|---|---|---|---|
| Tỷ lệ 3 nhãn | Bar (count) + stacked 100% | Pie/donut | So sánh góc kém chính xác hơn so sánh độ dài; khó đặt Batch cạnh Stream |
| Theo thời gian | Line/area theo nhãn | Bar theo ngày | Line thể hiện xu hướng liên tục tốt hơn; bar dùng khi ít mốc |
| Platform × nhãn | Stacked bar 100% ngang | Heatmap | Heatmap hợp khi nhiều platform; hiện chỉ 1–2 nguồn |
| Sự kiện mới | Saved search (bảng) | Metric "last processed_at" | Bảng cho thấy chính event vừa gửi → bằng chứng trực quan khi demo |

## 6. Phương pháp benchmark

- p50/p95 bằng nearest-rank trên toàn bộ sự kiện của một lần chạy; ≥ 100 sự kiện/lần (lý tưởng ≥ 1.000); 3 lần lặp + 1 warm-up bỏ đi; báo trung vị và min–max.
- **Thay thế:** trung bình ± độ lệch chuẩn – dễ tính nhưng bị kéo lệch bởi vài sự kiện chậm (đuôi dài), che mất điều người dùng thấy. Vẫn ghi mean để tham khảo.
- Độ trễ chính thức đo ngoài (poll ES theo `event_id`, mili-giây), không dựa hoàn toàn vào `processed_at` (giây, gán theo batch).

## 7. Xác nhận dữ liệu đúng

1. Bảo toàn số lượng: `input = valid + invalid`; `valid = ES _count` cho phạm vi chạy.
2. Đối chiếu id (mất/trùng).
3. Đối chiếu nội dung mẫu: `text` gốc không bị đổi, timestamp đúng UTC.
4. Đối chiếu nhãn: phân bố nhãn trên dashboard = `terms` aggregation ES = thống kê của C trên cùng tập.

## 8. Hạn chế đã biết

- Một máy, Spark `local[*]`; không đo cluster.
- Dữ liệu stream hiện là giả lập 3 câu cố định; khác phân phối thật.
- Máy D cần cấu hình riêng (JDK 17 portable, winutils) – khác máy A, có thể ảnh hưởng so sánh số liệu giữa hai máy.
