
# W03 – Batch Processing Benchmark

## 1. Mục tiêu

Đánh giá hiệu quả đọc và quét dữ liệu lịch sử bằng
Apache Spark trên hai định dạng CSV và Parquet.

Thực nghiệm phục vụ việc phân tích đặc tính Volume
trong hệ thống Big Data Sentiment Analysis.

## 2. Môi trường thực nghiệm

- Công cụ: Apache Spark thông qua PySpark 3.5.1.
- Chế độ thực thi: local[2].
- Môi trường: Windows 11.
- Dataset: Sentiment140 Training.
- Số bản ghi: 1.600.000.
- Định dạng đầu vào: CSV.
- Định dạng sau xử lý: Parquet với nén Snappy.

Thử nghiệm được thực hiện cục bộ trên một máy,
không phải cụm Spark phân tán nhiều máy.

## 3. Phương pháp benchmark

Hai định dạng được đánh giá bằng cùng một tác vụ:
đếm số bản ghi và tính tổng số ký tự của cột text.

Không sử dụng riêng count() vì Parquet có thể
tối ưu việc đếm dòng nhờ metadata.

Quy trình đo:
1. Khởi động SparkSession.
2. Thực hiện một lượt warm-up không tính kết quả.
3. Chạy ba lượt đo cho mỗi định dạng.
4. Ghi thời gian thực thi và throughput.
5. Sử dụng trung vị để so sánh.

Công thức:

Throughput = Số bản ghi / Thời gian thực thi

Speedup = Thời gian CSV / Thời gian Parquet

## 4. Kết quả thời gian thực thi

| Lần đo | CSV (giây) | Parquet (giây) |
|---|---:|---:|
| Warm-up | 4,038 | 1,333 |
| Lần 1 | 2,016 | 0,651 |
| Lần 2 | 2,049 | 0,615 |
| Lần 3 | 2,178 | 0,590 |
| Trung vị | 2,049 | 0,615 |

Warm-up không được đưa vào tính trung vị.

## 5. Kết quả throughput

- CSV: 780.869 bản ghi/giây.
- Parquet: 2.601.626 bản ghi/giây.
- Speedup theo trung vị: khoảng 3,33 lần.
- Thời gian thực thi giảm khoảng 70%.

## 6. Kết quả dung lượng lưu trữ

- CSV gốc: 227,74 MiB.
- Parquet sau chuẩn hóa: 113,76 MiB.
- Mức giảm dung lượng: 50,05%.
- Tỷ lệ kích thước: khoảng 2:1.

Hai phiên bản dữ liệu không có cấu trúc trường
hoàn toàn giống nhau. Vì vậy, mức giảm dung lượng
không phải tỷ lệ nén thuần túy của Snappy.

## 7. Kiểm định chất lượng Parquet

Dữ liệu Parquet đã được đọc lại và kiểm tra:

- Tổng bản ghi: 1.600.000.
- Event ID rỗng: 0.
- Event ID trùng: 0.
- Text rỗng: 0.
- Timestamp sai định dạng: 0.
- Nhãn không hợp lệ: 0.
- Negative: 800.000.
- Positive: 800.000.

Kết quả: 7/7 tiêu chí kiểm định đạt yêu cầu.

## 8. Nhận xét

Trong điều kiện thực nghiệm, Parquet cho thời gian
đọc và quét văn bản thấp hơn CSV ở cả ba lần đo.

Kết quả cho thấy định dạng lưu trữ dạng cột có
lợi thế đối với tác vụ phân tích được khảo sát.

Quy trình Batch đã xử lý, chuẩn hóa và lưu trữ
thành công 1.600.000 bản ghi dữ liệu lịch sử.

## 9. Hạn chế

- Benchmark chỉ thực hiện trên một máy.
- Số lần đo còn ít.
- CSV luôn được đo trước Parquet trong mỗi vòng.
- Bộ nhớ đệm và tác vụ nền có thể ảnh hưởng kết quả.
- Chỉ đo tác vụ đọc và quét cột text.
- Chưa đo thời gian ETL đầu cuối.
- Chưa đánh giá khả năng mở rộng trên nhiều máy.

Do đó, không khái quát tốc độ tăng 3,33 lần cho
mọi môi trường và mọi tác vụ Spark.

## 10. Kết luận

Batch Processing đã hoạt động thành công trên
1,6 triệu bản ghi Sentiment140.

Dữ liệu được chuẩn hóa về schema chung và lưu
dưới định dạng Parquet với nén Snappy.

Trong phép thử đọc và quét văn bản trên Spark
local[2], Parquet đạt thời gian trung vị 0,615 giây,
so với 2,049 giây của CSV.

Kết quả cung cấp bằng chứng thực nghiệm bước đầu
cho khả năng xử lý Volume của hệ thống.
