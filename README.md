# Hệ thống Big Data Sentiment Pipeline (Nhóm 24)

Kiến trúc xử lý dữ liệu thời gian thực (Real-time Streaming) phân tích cảm xúc đánh giá của người dùng.

## Yêu cầu hệ thống
- **Python:** Phiên bản 3.12 (Khuyên dùng Miniconda)
- **Docker Desktop:** Bắt buộc phải bật để chạy hạ tầng lõi.
- **Thư viện Python:** Chạy lệnh sau để cài đặt:
  ```bash
  pip install pyspark==3.5.1 kafka-python
  ```

## Hướng dẫn khởi chạy (Local)

**Bước 1: Khởi động hạ tầng lõi (Kafka, Zookeeper, Elasticsearch)**
Mở Terminal tại thư mục gốc của dự án và chạy:
```bash
docker compose up -d
```

**Bước 2: Cấu hình môi trường Spark (ĐẶC BIỆT LƯU Ý CHO WINDOWS)**
Nếu bạn dùng hệ điều hành Windows, **bắt buộc** phải chạy lệnh dưới đây để tải công cụ giả lập môi trường Linux (`winutils`). Nếu dùng MacOS/Linux thì bỏ qua bước này.
```bash
python processing/setup_hadoop.py
```

**Bước 3: Kích hoạt luồng dữ liệu (Chia đôi Terminal)**
- Mở **Terminal 1** (Spark lắng nghe dữ liệu): 
  ```bash
  python processing/spark_streaming.py
  ```
- Mở **Terminal 2** (Khởi động Producer bơm dữ liệu):
  ```bash
  python ingestion/test_producer.py
  ```