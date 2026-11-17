# W01 – Kiến trúc hệ thống và giải trình phương pháp

## 1. Mục tiêu dự án

Dự án “Ứng dụng Big Data và Machine Learning trong Phân tích Cảm xúc dư luận” hướng đến xây dựng hệ thống có khả năng thu thập, xử lý và phân tích nội dung văn bản từ mạng xã hội.

Hệ thống được thiết kế với hai nhánh xử lý:

- **Batch Processing:** Xử lý tập dữ liệu lịch sử theo từng đợt.
- **Stream Processing:** Tiếp nhận và xử lý dữ liệu mới phát sinh liên tục.

Cả hai nhánh hướng đến sử dụng chung mô hình Machine Learning để phân loại văn bản thành ba nhóm cảm xúc: Positive, Negative và Neutral.

Dự án tập trung kiểm chứng ba đặc trưng Big Data: Volume, Velocity và Variety.

## 2. Kiến trúc tổng thể

### 2.1. Batch Processing – Dự kiến triển khai

Nguồn dữ liệu lịch sử (CSV/JSON) → PySpark Batch → Làm sạch và chuẩn hóa → Lưu Parquet → Machine Learning → Elasticsearch → Kibana.

Batch Processing phục vụ phân tích dữ liệu lịch sử, thống kê cảm xúc và đánh giá hiệu năng khi khối lượng dữ liệu tăng.

### 2.2. Stream Processing – Đã có nguyên mẫu hoạt động

Kafka Producer → Apache Kafka → Spark Structured Streaming → Elasticsearch → Kibana.

Dữ liệu mẫu được Producer gửi vào topic `social_events_v1`. Spark Structured Streaming tiếp nhận, phân tích cấu trúc JSON và ghi dữ liệu sang Elasticsearch bằng Bulk API.

Kibana được sử dụng để kiểm tra và trực quan hóa các sự kiện đã được lưu.

Hiện tại, dữ liệu Streaming là dữ liệu mô phỏng, chưa phải dữ liệu thực tế được thu thập từ API mạng xã hội. Pipeline cũng chưa tích hợp dự đoán cảm xúc bằng Machine Learning.

## 3. Các phương pháp và lý do lựa chọn

### 3.1. Apache Kafka

**Phương pháp:** Sử dụng hệ thống truyền và lưu trữ luồng sự kiện theo mô hình Producer–Topic–Consumer.

**Lý do lựa chọn:** Kafka giúp tách biệt chương trình thu thập dữ liệu khỏi chương trình xử lý. Khi tốc độ dữ liệu đầu vào khác tốc độ xử lý, Kafka có thể lưu các sự kiện theo chính sách retention đã cấu hình để Consumer tiếp tục đọc.

**Phương án thay thế:** Gửi dữ liệu trực tiếp đến chương trình xử lý hoặc sử dụng một hệ thống hàng đợi khác.

**Hạn chế:** Kafka cần cấu hình broker, partition, retention và quản lý tài nguyên.

### 3.2. Apache Spark Structured Streaming

**Phương pháp:** Xử lý dữ liệu liên tục dưới dạng micro-batch.

**Lý do lựa chọn:** Spark Structured Streaming hỗ trợ xử lý dữ liệu có cấu trúc bằng DataFrame, tích hợp được với Kafka và thuộc cùng hệ sinh thái với PySpark Batch.

**Phương án thay thế:** Xây dựng Consumer xử lý bằng Python thuần hoặc sử dụng một nền tảng stream processing khác như Apache Flink.

**Hạn chế:** Micro-batch tạo ra độ trễ xử lý; hiệu năng phụ thuộc cấu hình Spark, kích thước batch và tốc độ xử lý các tác vụ.

### 3.3. PySpark Batch

**Phương pháp dự kiến:** Sử dụng Spark DataFrame để đọc, làm sạch, chuẩn hóa, tổng hợp và lưu dữ liệu lịch sử.

**Lý do lựa chọn:** PySpark hỗ trợ xử lý dữ liệu song song, có thể mở rộng sang môi trường cluster và giúp thống nhất công nghệ xử lý giữa Batch và Streaming.

**Phương án thay thế:** pandas hoặc các công cụ xử lý dữ liệu theo lô khác.

**Hạn chế:** Spark có chi phí khởi tạo và quản lý tác vụ; không phải lúc nào cũng hiệu quả hơn pandas đối với tập dữ liệu nhỏ.

### 3.4. Elasticsearch và Kibana

**Phương pháp:** Lưu trữ kết quả xử lý trong Elasticsearch, sử dụng Kibana để truy vấn và trực quan hóa.

**Lý do lựa chọn:** Elasticsearch hỗ trợ truy vấn, lọc và tổng hợp dữ liệu. Kibana hỗ trợ xây dựng Dashboard để theo dõi số lượng, nguồn và xu hướng của các sự kiện.

**Phương án thay thế:** Cơ sở dữ liệu quan hệ kết hợp công cụ trực quan hóa khác.

**Hạn chế:** Elasticsearch cần quản lý mapping, tài nguyên lưu trữ và chính sách index.

### 3.5. foreachBatch và Elasticsearch Bulk API

**Phương pháp hiện tại:** Spark xử lý từng micro-batch và sử dụng Python để ghi dữ liệu sang Elasticsearch thông qua Bulk API.

**Lý do lựa chọn:** Nhóm từng gặp lỗi tương thích khi thử Elasticsearch Spark Connector. Sử dụng `foreachBatch` với Bulk API giúp nguyên mẫu có thể hoạt động trên môi trường hiện tại.

**Phương án thay thế:** Sử dụng Spark Connector tương thích hoặc xây dựng cơ chế ghi phân tán theo partition.

**Hạn chế:** Cách sử dụng `toLocalIterator()` hiện tại đưa việc ghi qua driver, có thể trở thành nút thắt cổ chai khi tăng quy mô dữ liệu. Cần tối ưu và kiểm tra khả năng xử lý lại dữ liệu trước khi thử nghiệm tải lớn.

## 4. Phương pháp kiểm chứng 3V

### 4.1. Volume

Thử nghiệm xử lý các tập dữ liệu lịch sử với quy mô tăng dần bằng PySpark Batch.

Các chỉ số dự kiến gồm số bản ghi xử lý, thời gian thực thi, thông lượng và tài nguyên sử dụng.

### 4.2. Velocity

Thử nghiệm gửi sự kiện vào Kafka ở nhiều tốc độ khác nhau.

Các chỉ số dự kiến gồm tốc độ gửi, tốc độ xử lý, độ trễ, dữ liệu tồn đọng và tỷ lệ lỗi.

### 4.3. Variety

Thử nghiệm các nguồn dữ liệu có định dạng và cấu trúc khác nhau, chẳng hạn CSV và JSON, với các trường thiếu, văn bản chứa URL, hashtag, emoji hoặc ký tự đặc biệt.

Đánh giá khả năng chuyển đổi về schema chung và tỷ lệ bản ghi được xử lý hợp lệ.

## 5. Kết quả kiểm thử hiện tại

Trong lần kiểm thử ngày 17/11/2026:

- Spark Streaming v2 khởi động thành công.
- Producer gửi ba sự kiện mẫu mới vào Kafka.
- Elasticsearch Index `social_events_v1` tăng từ 6 lên 9 bản ghi.
- Kibana Discover hiển thị ba sự kiện mới trong khoảng thời gian kiểm tra.
- Các sự kiện có trường `created_at`, `collected_at` và `processed_at`.
- Chênh lệch giữa thời điểm thu thập và thời điểm xử lý được quan sát khoảng 5–6 giây.

Kết quả xác nhận nguyên mẫu Streaming có thể tiếp nhận và ghi các sự kiện mới.

Độ trễ trên mới là kết quả sơ bộ, chưa đại diện cho hiệu năng tổng thể hoặc độ trễ end-to-end đến khi Elasticsearch cho phép truy vấn.

## 6. Giới hạn và công việc tiếp theo

- Spark Streaming hiện chạy bằng `local[*]`, chưa kiểm chứng thực thi phân tán trên Spark cluster trong Docker.
- Chưa có Batch Processing hoàn chỉnh.
- Chưa có mô hình Machine Learning phân loại cảm xúc.
- Chưa tích hợp dữ liệu động từ API mạng xã hội.
- Chưa thực hiện benchmark Volume, Velocity và Variety ở quy mô chính thức.

Các giai đoạn tiếp theo tập trung vào lựa chọn và khảo sát dataset, xây dựng Batch Processing, huấn luyện mô hình Machine Learning ba nhãn và tích hợp kết quả vào hệ thống chung.