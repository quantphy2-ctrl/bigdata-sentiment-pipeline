# W01 - Streaming Pipeline Verification

## 1. Mục tiêu
Kiểm chứng pipeline xử lý dữ liệu Streaming từ
Kafka Producer đến Kibana.

## 2. Công nghệ
- Apache Kafka
- Apache Spark Structured Streaming 3.5.1
- Elasticsearch 7.17.10
- Kibana 7.17.10
- Python 3.11

## 3. Quy trình kiểm thử
1. Khởi động Docker Compose.
2. Chạy Spark Streaming v2.
3. Chạy Kafka Producer v2.
4. Gửi 3 sự kiện JSON mới.
5. Kiểm tra Elasticsearch.
6. Kiểm tra Kibana Discover.

## 4. Kết quả
- Elasticsearch trước kiểm thử: 6 bản ghi.
- Elasticsearch sau kiểm thử: 9 bản ghi.
- Sự kiện mới: 3.
- Kafka topic: social_events_v1.
- Nguồn dữ liệu: simulated_reddit.
- Độ trễ quan sát sơ bộ: khoảng 5–6 giây.
- Kibana hiển thị đầy đủ 3 sự kiện mới.

## 5. Đánh giá
Pipeline Streaming v2 đã tiếp nhận và xử lý
thành công dữ liệu mô phỏng.

## 6. Giới hạn
- Chưa sử dụng dữ liệu API thực tế.
- Chưa tích hợp Machine Learning.
- Spark đang chạy local[*].
- Chưa thực nghiệm Velocity ở quy mô lớn.
- Độ trễ đo bằng timestamp chưa phải độ trễ
  end-to-end đến khi Elasticsearch có thể truy vấn.
