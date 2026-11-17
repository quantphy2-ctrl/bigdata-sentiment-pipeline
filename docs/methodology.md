# Methodology and Technical Decisions

## 1. Mục đích

Tài liệu giải thích các lựa chọn kỹ thuật trong quá trình xây dựng Big Data Sentiment Pipeline. Mỗi lựa chọn gồm:
- Lý do lựa chọn.
- Phương án thay thế.
- Hạn chế và rủi ro.
- Cách giảm thiểu rủi ro.

## 2. Các quyết định kỹ thuật

### 2.1. Chọn hai dataset chính: Airline Tweets và Sentiment140

**Lựa chọn**

- Airline Tweets: dataset có ba nhóm sentiment, phù hợp khảo sát phân phối nhãn và thử nghiệm bài toán phân loại nhiều lớp.
- Sentiment140: dataset lớn, phù hợp kiểm tra khả năng xử lý khối lượng dữ liệu.

**Lý do**

Hai dataset bổ sung cho nhau:
- Airline Tweets có quy mô nhỏ hơn và có đủ ba nhóm sentiment.
- Sentiment140 train có 1,6 triệu dòng, phù hợp kiểm thử xử lý dữ liệu lớn.

**Phương án thay thế**

- Chỉ dùng Airline Tweets: đơn giản hơn nhưng không đủ đại diện cho bài kiểm thử volume lớn.
- Chỉ dùng Sentiment140: có khối lượng lớn nhưng train chủ yếu chỉ có hai lớp positive và negative.

**Hạn chế**

- Hai dataset khác nhau về nguồn, thời gian thu thập và phân phối nhãn.
- Sentiment140 train không có lớp neutral.
- Nhãn Sentiment140 train được tạo bằng distant supervision dựa trên emoticon nên có thể nhiễu.
- Dữ liệu mạng xã hội cũ có thể không đại diện cho ngôn ngữ hiện tại.

**Giảm thiểu**

- Giữ thông tin `source_dataset`.
- Không gộp phân phối nhãn giữa các dataset mà không phân biệt nguồn.
- Không tự tạo nhãn neutral cho Sentiment140 train.
- Báo cáo kết quả riêng theo từng dataset.

### 2.2. Dùng Replay làm đường chạy chính

**Lựa chọn**

Dùng dữ liệu đã tải và lưu cục bộ để replay pipeline.

**Lý do**

- Kết quả có thể tái lập.
- Không phụ thuộc kết nối Internet hoặc API key.
- Phù hợp kiểm thử Spark, Parquet, Elasticsearch và dashboard.
- Dễ đối soát số lượng record giữa các bước.

**Phương án thay thế**

Polling API liên tục từ nền tảng mạng xã hội.

**Hạn chế**

- Replay không phản ánh hoàn toàn tính biến động của dữ liệu thời gian thực.
- Phải quản lý phiên bản và nguồn gốc file dữ liệu.

**Giảm thiểu**

Lưu metadata của dataset, cấu hình chạy, thời gian chạy và số dòng đầu vào/đầu ra.

### 2.3. Thiết kế API Polling như một nguồn mở rộng

**Lựa chọn**

Ưu tiên thử nghiệm API đọc công khai của Bluesky; Mastodon là phương án dự phòng.

**Lý do**

- Có tài liệu API chính thức.
- Có thể lấy dữ liệu mới để minh họa ingestion.
- Có thể lưu raw response và replay lại.

**Phương án thay thế**

- Dùng file CSV có sẵn.
- Dùng dữ liệu JSONL giả lập có cấu trúc tương tự API.
- Dùng Mastodon nếu nguồn API chính không khả dụng.

**Hạn chế**

- API có thể thay đổi hoặc giới hạn tốc độ.
- Dữ liệu API không có nhãn sentiment chuẩn.
- Dữ liệu của các nền tảng khác nhau có thể khác ngôn ngữ và đặc điểm người dùng.

**Giảm thiểu**

- Có timeout, retry có giới hạn và backoff.
- Có chế độ replay độc lập.
- Tách nhãn gốc, nhãn thủ công và nhãn dự đoán.
- Không coi dự đoán của model là ground truth.

### 2.4. Chọn CSV làm định dạng đầu vào

**Lựa chọn**

Dùng CSV cho dữ liệu nguồn đã thu thập.

**Lý do**

- Phổ biến, dễ kiểm tra.
- Tương thích với Python, Pandas và Spark.
- Thuận tiện cho quá trình khảo sát và đối chiếu dữ liệu.

**Phương án thay thế**

JSONL hoặc Avro cho dữ liệu dạng event/API.

**Hạn chế**

- CSV không biểu diễn tốt cấu trúc lồng nhau.
- Encoding, delimiter và kiểu dữ liệu có thể không đồng nhất.
- Kiểu dữ liệu có thể phải suy luận khi đọc.

**Giảm thiểu**

- Khai báo encoding theo từng dataset.
- Kiểm tra header và schema trước khi xử lý.
- Khai báo kiểu dữ liệu quan trọng rõ ràng.
- Chuẩn hóa dữ liệu sau bước đọc.

### 2.5. Chọn Parquet cho dữ liệu trung gian

**Lựa chọn**

Dùng Parquet để lưu dữ liệu sau chuẩn hóa.

**Lý do**

- Hỗ trợ schema và kiểu dữ liệu.
- Phù hợp xử lý phân tán với Spark.
- Có khả năng nén và đọc theo cột.
- Thuận tiện cho các bước phân tích tiếp theo.

**Phương án thay thế**

CSV, JSONL hoặc ORC.

**Hạn chế**

- Khó đọc trực tiếp bằng trình soạn thảo văn bản.
- Cần công cụ tương thích để kiểm tra.
- Số lượng file nhỏ quá nhiều có thể làm tăng overhead.

**Giảm thiểu**

- Có script kiểm tra số dòng và schema.
- Tổ chức thư mục output theo từng giai đoạn.
- Không commit dữ liệu Parquet lớn nếu repository chỉ cần mã nguồn và báo cáo.

### 2.6. Chọn PySpark cho xử lý dữ liệu

**Lựa chọn**

Dùng PySpark để đọc, chuẩn hóa và tổng hợp dữ liệu.

**Lý do**

- Hỗ trợ xử lý phân tán.
- Có DataFrame API.
- Có thể mở rộng khi dữ liệu tăng.
- Tích hợp với Parquet và hệ sinh thái Hadoop.

**Phương án thay thế**

- Pandas: dễ phát triển và phù hợp dữ liệu nhỏ.
- Dask: hỗ trợ tính toán song song trên Python.
- Apache Flink: phù hợp một số hệ thống streaming.

**Hạn chế**

- Tốn tài nguyên và có chi phí khởi tạo.
- Cấu hình Java/Hadoop trên Windows có thể phức tạp.
- Với dataset nhỏ, Spark có thể chậm hơn Pandas do overhead.

**Giảm thiểu**

- Có smoke test quy mô nhỏ.
- Kiểm tra schema trước khi chạy job lớn.
- Theo dõi memory và số partition.
- Tách bước đọc dữ liệu, transform và ghi output.

### 2.7. Chọn Elasticsearch cho kết quả phân tích

**Lựa chọn**

Dùng Elasticsearch lưu các kết quả aggregation phục vụ truy vấn và dashboard.

**Lý do**

- Hỗ trợ truy vấn dữ liệu dạng document.
- Có thể tích hợp Kibana.
- Phù hợp hiển thị số liệu theo thời gian và nhóm sentiment.

**Phương án thay thế**

PostgreSQL, ClickHouse hoặc lưu kết quả aggregate thành Parquet/CSV.

**Hạn chế**

- Tốn bộ nhớ và tài nguyên.
- Cần quản lý mapping, index và vòng đời dữ liệu.
- Trạng thái cluster một node có thể là yellow do replica chưa được phân bổ; cần đánh giá theo cấu hình cụ thể.

**Giảm thiểu**

- Chỉ index dữ liệu đã tổng hợp nếu mục tiêu là dashboard.
- Tạo mapping rõ ràng.
- Có script tạo index và nạp lại dữ liệu.
- Đối soát document count sau khi load.

### 2.8. Deduplication theo định danh nguồn

**Lựa chọn**

Ưu tiên ID ổn định của bản ghi nguồn làm khóa chống trùng.

**Lý do**

- Tránh tính hai lần cùng một bài đăng.
- Hữu ích khi polling API nhiều lần.
- Hỗ trợ đối soát dữ liệu.

**Phương án thay thế**

Hash nội dung text và timestamp.

**Hạn chế**

- Một số dataset có ID thiếu hoặc không duy nhất.
- Hai bài đăng khác nhau có thể có cùng nội dung.
- Nội dung chỉnh sửa có thể tạo ra khác biệt hash.

**Giảm thiểu**

- Dùng khóa ghép khi không có ID ổn định.
- Lưu `source` cùng ID để tránh xung đột giữa các nguồn.
- Không loại bản ghi chỉ vì text giống nhau nếu chưa xác định quy tắc nghiệp vụ.

### 2.9. Tách nhãn sentiment và nhãn dự đoán

**Lựa chọn**

Tách riêng nhãn có sẵn, nhãn thủ công và kết quả dự đoán.

**Lý do**

Tránh nhầm lẫn giữa ground truth và output của mô hình.

**Phương án thay thế**

Dùng chung một trường label cho tất cả nguồn.

**Hạn chế**

Schema phức tạp hơn và cần quy định rõ nguồn nhãn.

**Giảm thiểu**

Quy định `label_source`, `sentiment_label` và trường prediction riêng theo `docs/data_schema.md`.

## 3. Nguyên tắc đánh giá

1. Không tự tạo dữ liệu hoặc nhãn mà không ghi rõ phương pháp.
2. Phân biệt dữ liệu gốc, dữ liệu đã chuẩn hóa và dữ liệu tổng hợp.
3. Mỗi bước xử lý cần có số liệu đối soát.
4. Mỗi test case phải có trạng thái thực thi và bằng chứng.
5. Khi API lỗi, pipeline vẫn phải chạy được bằng replay.
6. Không đánh giá mô hình bằng dữ liệu không có ground truth đáng tin cậy.

## 4. Tài liệu tham khảo

- Sentiment140 dataset card: https://huggingface.co/datasets/stanfordnlp/sentiment140
- Bluesky API reference: https://docs.bsky.app/docs/api/app-bsky-feed-get-feed
- Bluesky rate limits: https://bsky.network/docs/rate-limits/
- Mastodon timelines API: https://docs.joinmastodon.org/methods/timelines/
- Mastodon rate limits: https://docs.joinmastodon.org/api/rate-limits/

## 5. Những điểm cần xác minh trước khi nghiệm thu

- Đối chiếu tên trường trong tài liệu với `docs/data_schema.md`.
- Xác minh nguồn và điều khoản sử dụng của từng bản dataset đang lưu.
- Chạy thử API và lưu log request/response đã loại bỏ thông tin nhạy cảm.
- Chạy test cases và cập nhật trạng thái PASS/FAIL/NOT RUN.
- Ghi lại giới hạn thực tế về thời gian chạy và tài nguyên máy.
