# Big Data Sentiment Pipeline – Nhóm 24

> **Hướng dẫn cài đặt và chạy dự án dành cho thành viên nhóm.**  
> Cập nhật: 17/11/2026 · Môi trường đã thử nghiệm bởi nhóm trưởng: **Windows + Python 3.11 + PySpark 3.5.1**.  
> **Đọc mục [Trạng thái dự án](#2-trạng-thái-dự-án) trước:** hệ thống hiện có pipeline **Streaming v2 với dữ liệu mô phỏng**, chưa phải hệ thống phân tích cảm xúc hoàn chỉnh.


## 3. Cấu trúc repository

```text
bigdata-sentiment-pipeline/
├── batch_processing/             # Dành cho nhánh Batch; chưa có pipeline hoàn chỉnh
├── docker/
│   └── docker-compose.yml        # 6 dịch vụ Docker
├── docs/
│   └── data_schema.md            # Data Schema v1.0
├── ingestion/
│   ├── test_producer.py          # Producer mẫu v1 (legacy)
│   └── test_producer_v2.py       # Producer JSON v2 (đang sử dụng)
├── processing/
│   ├── setup_hadoop.py           # Script Windows cũ – xem lưu ý bảo mật phía dưới
│   ├── spark_streaming.py        # Pipeline v1 (legacy)
│   └── spark_streaming_v2.py     # Streaming v2 (đang sử dụng)
├── kibana/
│   └── group24-dashboard.ndjson  # Saved Objects v1 (không chứa dữ liệu ES)
├── scripts/
│   └── create_es_index.ps1       # File bổ sung kèm README mới
├── serving/
├── streaming/
├── .gitignore
├── requirements.txt
└── README.md
```

> `scripts/create_es_index.ps1` **là file mới đi kèm bộ README cập nhật**.

## 4. Yêu cầu trước khi cài đặt

Hướng dẫn bên dưới dành cho **Windows 10/11, PowerShell và VS Code**. Không đặt project trong nhiều thư mục trùng tên lồng nhau.

| Thành phần | Yêu cầu |
|---|---|
| Git | Đã cài, chạy được `git --version` |
| Docker Desktop | Đang chạy, dùng Linux containers |
| Python | **3.11 x64** (chọn bằng `py -3.11`) |
| Java | **JDK 17**, có `JAVA_HOME`/`PATH` phù hợp |
| PySpark | **3.5.1**, theo `requirements.txt` |
| Internet | Cần khi tải Docker images và Maven Kafka connector lần đầu |
| Tài nguyên | Khuyến nghị RAM **từ 8 GB** và có đủ dung lượng trống; 16 GB thuận lợi hơn |

Kiểm tra trong **PowerShell**:

```powershell
git --version
docker --version
docker compose version
py -0p
java -version
$env:JAVA_HOME
```


## 5. Cài đặt sạch từ GitHub 

**Bước 1 – Clone repo vào thư mục riêng** (ví dụ dưới đây tránh lỗi thư mục lồng nhau):

```powershell
New-Item -ItemType Directory -Path C:\BigData -Force | Out-Null
Set-Location C:\BigData
git clone https://github.com/quantphy2-ctrl/bigdata-sentiment-pipeline.git
Set-Location .\bigdata-sentiment-pipeline
```

Kiểm tra đang đứng **đúng thư mục gốc repository**:

```powershell
git rev-parse --show-toplevel
Test-Path .\docker\docker-compose.yml
Test-Path .\ingestion\test_producer_v2.py
Test-Path .\processing\spark_streaming_v2.py
Test-Path .\scripts\create_es_index.ps1
```

Bốn lệnh `Test-Path` cần trả về `True`. Nếu script cuối trả về `False`, **chưa cập nhật đủ bộ README + script** lên `main`.

**Bước 2 – Tạo môi trường ảo Python 3.11 ngay trong repo:**

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -c "import pyspark; print('PySpark:', pyspark.__version__)"
```

Kết quả mong đợi: `PySpark: 3.5.1`. Trong VS Code chọn **Python: Select Interpreter → `.venv\Scripts\python.exe`**.

**Bước 3 – Khởi động Docker Desktop** và từ **thư mục gốc repo** chạy:

```powershell
docker compose -f .\docker\docker-compose.yml config --quiet
docker compose -f .\docker\docker-compose.yml up -d
docker compose -f .\docker\docker-compose.yml ps
```

Các dịch vụ/địa chỉ chính:

| Dịch vụ | Địa chỉ trên máy Windows |
|---|---|
| Kafka | `localhost:9092` (không có trang web) |
| Elasticsearch | http://localhost:9200 |
| Kibana | http://localhost:5601 |
| Spark Master UI (container) | http://localhost:8080 |

Kiểm tra Elasticsearch phản hồi:

```powershell
Invoke-RestMethod http://localhost:9200
```

> **Chú ý:** Spark Master/Worker container được khởi động, nhưng luồng v2 hiện chạy ở chế độ `local[*]`. Trang Spark Master UI không phải bằng chứng Spark v2 đang chạy trên cluster.

**Bước 4 – Tạo index Elasticsearch v2 với mapping chính xác:**

```powershell
.\scripts\create_es_index.ps1
```

Lệnh này **không xóa dữ liệu**. Nếu index đã tồn tại, script sẽ kiểm tra các trường `created_at`, `collected_at`, `processed_at` có kiểu `date` và báo lỗi nếu mapping sai. Không tự ý xóa index để làm lại.

**Bước 5 – Tạo Kafka topic và gửi ba sự kiện mẫu lần đầu:**

```powershell
.\.venv\Scripts\python.exe .\ingestion\test_producer_v2.py
```

Producer tự tạo topic `social_events_v1` với **3 partition**, sau đó gửi 3 sự kiện giả lập. Mỗi lần chạy dùng `event_id` mới. Dữ liệu mẫu có `platform=simulated_reddit`, **không phải dữ liệu đang lấy trực tiếp từ Reddit API**.

**Bước 6 – Chạy Spark Streaming v2 ở Terminal thứ hai, vẫn tại repo:**

```powershell
.\.venv\Scripts\python.exe .\processing\spark_streaming_v2.py
```

Kết quả ví dụ:

```text
Spark Streaming v2 dang hoat dong...
Kafka: social_events_v1
Elasticsearch: social_events_v1
Batch 0: da ghi 3 su kien vao social_events_v1
```

Vì `startingOffsets=earliest`, trong **lần khởi chạy với checkpoint mới**, Spark có thể đọc sự kiện đã gửi trước đó. Số bản ghi thực tế có thể khác nếu topic chứa dữ liệu cũ. Để dừng Spark, nhấn **Ctrl+C** trong Terminal đang chạy chương trình.

**Bước 7 – Kiểm chứng Elasticsearch bằng Terminal thứ ba:**

```powershell
Invoke-RestMethod "http://localhost:9200/social_events_v1/_count"

$result = Invoke-RestMethod "http://localhost:9200/social_events_v1/_search?size=10"
$result.hits.hits | ForEach-Object { $_._source } | Format-List
```

Trên môi trường mới, sau lần đầu nên có khoảng **3 tài liệu**. Nội dung mỗi tài liệu có `event_id`, `platform`, `text`, `created_at`, `collected_at`, `processed_at`, `engagement`, `kafka_topic`, `kafka_partition`, `kafka_offset`.

**Bước 8 – Chứng minh dữ liệu mới đi qua luồng đang chạy:**

Giữ Terminal Spark chạy, mở Terminal khác và gửi tiếp:

```powershell
.\.venv\Scripts\python.exe .\ingestion\test_producer_v2.py
Invoke-RestMethod "http://localhost:9200/social_events_v1/_count"
```

Nếu trước đó có 3 tài liệu và Producer gửi 3 sự kiện mới có ID duy nhất, tổng số tài liệu **dự kiến** là 6 sau khi Spark xử lý xong. Đợi một nhịp xử lý và kiểm tra lại nếu truy vấn quá sớm.

## 6. Xem dữ liệu trên Kibana

1. Mở **http://localhost:5601**.
2. Vào **Stack Management → Index Patterns → Create index pattern**.
3. Tên: **`social_events_v1`**; chọn **Timestamp field: `created_at`**.
4. Nếu Kibana báo **index pattern đã tồn tại**, không cần tạo lại: vào **Analytics → Discover** và chọn `social_events_v1`.
5. Chọn khoảng thời gian **Last 7 days** (hoặc khoảng bao trùm `created_at`) rồi nhấn **Refresh**.
6. Kiểm tra nội dung sự kiện và ba trường `created_at`, `collected_at`, `processed_at`.

Kibana có thể hiển thị giờ theo múi giờ trình duyệt; bản ghi JSON dùng giờ **UTC**. Nếu trống do khoảng thời gian, tăng time range trước khi kết luận không có dữ liệu.

**Khôi phục Dashboard v1 (tùy chọn):** **Stack Management → Saved Objects → Import**, chọn `kibana/group24-dashboard.ndjson`. File này dành cho **index `sentiment_data` (v1)**, không phải dashboard phân tích `social_events_v1` hoàn chỉnh; **file `.ndjson` không chứa các bản ghi Elasticsearch**.

## 7. Data Schema v1.0 và ý nghĩa thời gian

Xem quy ước chi tiết tại [`docs/data_schema.md`](docs/data_schema.md). Ví dụ sự kiện giả lập:

```json
{
  "event_id": "demo_abc123",
  "platform": "simulated_reddit",
  "content_type": "comment",
  "text": "The service was excellent!",
  "language": "en",
  "created_at": "2026-11-17T02:00:00Z",
  "collected_at": "2026-11-17T02:00:00Z",
  "engagement": {"likes": null, "replies": null, "shares": null}
}
```

- `created_at`: thời điểm nội dung xuất hiện theo nguồn; ví dụ Producer demo dùng thời gian tạo giả lập.
- `collected_at`: thời điểm hệ thống thu thập/tạo sự kiện.
- `processed_at`: thời điểm Spark **bắt đầu ghi micro-batch** (được bổ sung vào Elasticsearch); **không** phải thời điểm Elasticsearch hoàn tất lưu.
- `event_id`: ID dùng làm `_id` của Elasticsearch để hạn chế tạo tài liệu trùng khi xử lý lại.

**Hiện chưa có `sentiment_label` hoặc `sentiment_confidence` do mô hình NLP chưa tích hợp.** Không suy diễn mô hình đã phân loại cảm xúc chỉ từ ba câu demo.
