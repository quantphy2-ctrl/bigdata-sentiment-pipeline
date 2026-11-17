
# W04 – Machine Learning & Pipeline Integration Report

## 1. Mục tiêu

Xây dựng mô hình Machine Learning để phân loại cảm xúc
văn bản thành ba nhãn: Negative, Neutral và Positive.

Đánh giá hiệu quả mô hình và thử nghiệm khả năng sử dụng
chung mô hình trong hai nhánh Batch và Streaming.

## 2. Dữ liệu sử dụng

Dataset: Twitter US Airline Sentiment.

- Dữ liệu ban đầu: 14.640 tweet.
- Dữ liệu không hợp lệ: 0 dòng.
- Nhóm văn bản mâu thuẫn nhãn: 25.
- Dòng bị loại do mâu thuẫn nhãn: 57.
- Dòng trùng cùng nhãn bị loại: 181.
- Tổng số dòng bị loại: 238.
- Dữ liệu sau làm sạch: 14.402 tweet.

Phân bố nhãn sau làm sạch:

| Nhãn | Số bản ghi |
|---|---:|
| Negative | 9.079 |
| Neutral | 3.046 |
| Positive | 2.277 |
| Tổng | 14.402 |

Các bản ghi có nội dung trùng nhưng khác nhãn
được loại khỏi tập dữ liệu ML.

Các bản ghi trùng nội dung và cùng nhãn chỉ giữ
một bản đại diện.

## 3. Phương pháp chia dữ liệu

Sử dụng Stratified Split với random_state = 42.

| Tập | Số bản ghi | Tỷ lệ |
|---|---:|---:|
| Train | 10.081 | Khoảng 70% |
| Validation | 2.160 | Khoảng 15% |
| Test | 2.161 | Khoảng 15% |

Phân bố ba nhãn được duy trì gần tương đương
giữa các tập.

Không phát hiện văn bản trùng chính xác giữa
Train, Validation và Test.

TF-IDF chỉ được fit trên dữ liệu huấn luyện,
không sử dụng Test để chọn tham số.

## 4. Phương pháp Machine Learning

### 4.1. TF-IDF

Sử dụng TfidfVectorizer để chuyển văn bản thành
vector đặc trưng số.

Cấu hình:

- ngram_range = (1, 2).
- min_df = 2.
- max_features = 30000.
- sublinear_tf = True.

### 4.2. Logistic Regression

Sử dụng Logistic Regression đa lớp với:

- max_iter = 1000.
- random_state = 42.
- class_weight = balanced.

Lý do lựa chọn:

- Phù hợp với dữ liệu văn bản biểu diễn bằng TF-IDF.
- Chi phí huấn luyện tương đối thấp.
- Dễ giải thích và tái sử dụng.
- Thích hợp làm mô hình baseline.

## 5. Kết quả mô hình Baseline

Đánh giá trên tập Validation gồm 2.160 tweet:

- Accuracy: 0,7972.
- Macro-F1: 0,7522.
- Thời gian huấn luyện: 1,360 giây.
- Số đặc trưng TF-IDF: 22.255.

F1-score theo nhãn:

- Negative: 0,8666.
- Neutral: 0,6343.
- Positive: 0,7556.

## 6. So sánh cấu hình

Bốn cấu hình được đánh giá trên cùng tập Validation:

| Cấu hình | Accuracy | Macro-F1 |
|---|---:|---:|
| Balanced, C=1.0 | 0,7972 | 0,7522 |
| Balanced, C=0.5 | 0,7940 | 0,7496 |
| Balanced, C=2.0 | 0,8019 | 0,7527 |
| Unweighted, C=1.0 | 0,7963 | 0,7135 |

Cấu hình được chọn:

- C = 2.0.
- class_weight = balanced.

Tiêu chí lựa chọn: Macro-F1 trên Validation.

Mức cải thiện Macro-F1 so với Baseline rất nhỏ,
chưa đủ để khẳng định cấu hình mới vượt trội ổn định.

## 7. Đánh giá cuối cùng trên Test

Mô hình được huấn luyện lại trên Train + Validation,
tổng cộng 12.241 tweet.

Tập Test gồm 2.161 tweet được sử dụng để đánh giá
cuối cùng sau khi đã chốt cấu hình.

Kết quả:

- Accuracy: 0,7927.
- Macro-F1: 0,7458.
- Thời gian huấn luyện: 1,375 giây.
- Số đặc trưng TF-IDF: 26.303.

### 7.1. Hiệu quả từng nhãn

| Nhãn | Precision | Recall | F1-score |
|---|---:|---:|---:|
| Negative | 0,8839 | 0,8443 | 0,8637 |
| Neutral | 0,6086 | 0,6499 | 0,6286 |
| Positive | 0,7151 | 0,7778 | 0,7451 |

### 7.2. Confusion Matrix

Hàng là nhãn thực tế, cột là nhãn dự đoán.

| Thực tế / Dự đoán | Negative | Neutral | Positive |
|---|---:|---:|---:|
| Negative | 1150 | 154 | 58 |
| Neutral | 112 | 297 | 48 |
| Positive | 39 | 37 | 266 |

Mô hình nhận diện Negative tốt nhất.
Neutral là nhãn có F1-score thấp nhất.

## 8. Lưu trữ mô hình

Mô hình được lưu tại:

models/airline_sentiment_v1.joblib

- Kích thước: khoảng 0,84 MiB.
- Công cụ: joblib.
- Bao gồm TF-IDF và Logistic Regression.
- Đã kiểm tra tải lại và dự đoán thành công.

File joblib được bỏ qua bởi .gitignore.

Để tái tạo mô hình trên máy khác, cần có dữ liệu
huấn luyện hợp lệ và chạy quy trình huấn luyện,
lưu mô hình tương ứng.

Chỉ tải file joblib từ nguồn đáng tin cậy.

## 9. Shared Inference

Module:

processing/sentiment_inference.py

Hàm:

predict_sentiments(texts)

Đầu ra gồm:

- sentiment_label.
- sentiment_confidence.
- processed_at.

Mô hình được cache trong tiến trình Python,
tránh tải lại ở mỗi lần dự đoán.

Confidence là xác suất ước lượng của mô hình,
chưa được hiệu chỉnh xác suất (calibration).

## 10. Thử nghiệm tích hợp Batch

Nguồn: Sentiment140 Parquet.

Quy trình:

PySpark đọc Parquet
-> lấy 6 tweet mẫu
-> Shared Inference
-> dự đoán cảm xúc.

Kết quả:

PASS: Batch Parquet -> Shared ML Inference.

Đây là smoke test trên 6 bản ghi.
Chưa thực hiện inference trên toàn bộ 1,6 triệu tweet.

## 11. Thử nghiệm tích hợp Streaming

Quy trình:

Kafka social_events_v1
-> Spark Structured Streaming
-> Shared ML Inference
-> Elasticsearch social_events_ml_v1
-> Kibana.

Phiên bản thử nghiệm được lưu tại:

processing/spark_streaming_ml.py

Streaming v2 gốc được giữ nguyên.

Mỗi nhóm tối đa 250 sự kiện được đưa vào
module inference trước khi gửi Elasticsearch Bulk API.

Kết quả:

- Kafka Producer gửi sự kiện thành công.
- Spark nhận và xử lý dữ liệu.
- Module ML bổ sung nhãn cảm xúc.
- Elasticsearch nhận document đã dự đoán.
- Kibana Discover hiển thị các trường cảm xúc.

Trong thử nghiệm Kibana, có 12 document
trong khoảng thời gian Last 24 hours.

Phân bố trên biểu đồ:
- Negative: 4.
- Neutral: 4.
- Positive: 4.

Nguồn dữ liệu kiểm thử là simulated_reddit,
không phải dữ liệu Reddit được thu thập qua API thật.

Số lượng document có thể bao gồm các sự kiện
Kafka cũ được xử lý lại bởi checkpoint mới.

## 12. Dashboard

Visualization:

W04 - Streaming Sentiment Distribution

Dashboard:

Big Data Sentiment Analysis - Streaming Dashboard

Biểu đồ sử dụng:
- Data View: social_events_ml_v1.
- Horizontal axis: sentiment_label.keyword.
- Vertical axis: Count of records.

Dashboard đã được lưu trên Kibana.

## 13. Hạn chế

- Mô hình huấn luyện chủ yếu trên tweet ngành hàng không.
- Dữ liệu Train mất cân bằng nhãn.
- Neutral có F1-score thấp hơn hai nhãn còn lại.
- Chưa đánh giá khả năng khái quát trên tập dữ liệu
  độc lập từ nhiều nền tảng mạng xã hội.
- Chưa kiểm tra đầy đủ văn bản gần trùng.
- Confidence chưa được hiệu chỉnh.
- Batch + ML mới được thử nghiệm trên 6 bản ghi.
- Streaming ML vẫn suy luận trên Spark driver,
  chưa triển khai inference phân tán trên worker.
- Nguồn Streaming hiện sử dụng Producer mô phỏng.
- Chưa thực hiện benchmark tải lớn cho Streaming ML.
- Chưa kiểm chứng khả năng tái triển khai hoàn chỉnh
  trên máy khác sau khi clone repository.

## 14. Kết luận

Tuần 4 đã xây dựng và đánh giá thành công mô hình
TF-IDF kết hợp Logistic Regression phân loại ba nhãn.

Mô hình cuối đạt Accuracy 0,7927 và Macro-F1 0,7458
trên tập Test gồm 2.161 tweet.

Shared Inference đã hoạt động độc lập và được kiểm tra
tích hợp với cả Batch Parquet và Streaming Kafka.

Kết quả dự đoán của Streaming đã được ghi vào
Elasticsearch và hiển thị trên Kibana Dashboard.

Các kết quả trên xác nhận chức năng tích hợp bước đầu,
chưa chứng minh hiệu năng hoặc độ chính xác khi
triển khai ở quy mô lớn trong môi trường thực tế.
