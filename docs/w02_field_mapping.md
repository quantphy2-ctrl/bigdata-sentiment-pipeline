
# W02 – Thiết kế Data Mapping

## 1. Mục tiêu

Chuẩn hóa hai nguồn dữ liệu lịch sử:
- Twitter US Airline Sentiment.
- Sentiment140.

Dữ liệu sau chuẩn hóa phải tuân thủ schema đầu vào
của dự án, dựa trên docs/data_schema.md.

Các trường bổ sung phục vụ Batch và Machine Learning
phải được quy định rõ ràng.

## 2. Mapping Twitter US Airline Sentiment

| Trường gốc | Trường chuẩn | Quy tắc |
|---|---|---|
| tweet_id | source_record_id | Giữ mã tweet gốc |
| tweet_id + số dòng | event_id | Tạo ID duy nhất, ổn định |
| text | text | Giữ nội dung văn bản |
| tweet_created | created_at | Chuyển sang ISO 8601 UTC |
| airline_sentiment | ground_truth_label | Chuẩn hóa nhãn về chữ thường |
| retweet_count | engagement.shares | Chuyển thành số nguyên nếu hợp lệ |
| Không có | platform | Gán "twitter" |
| Không có | content_type | Gán "post" |
| Không có | language | Gán "en" theo phạm vi dữ liệu tiếng Anh |
| Không có | collected_at | Thời điểm pipeline tiếp nhận bản ghi |
| Không có | engagement.likes | null |
| Không có | engagement.replies | null |

Các trường chứa thông tin tài khoản và vị trí không
được sử dụng làm đặc trưng mặc định cho mô hình ML.

Cần giữ bản dữ liệu gốc để đối chiếu.

## 3. Mapping Sentiment140

| Trường gốc | Trường chuẩn | Quy tắc |
|---|---|---|
| ids | source_record_id | Giữ mã tweet gốc |
| Nguồn + số dòng | event_id | Tạo ID duy nhất, ổn định |
| text | text | Giữ nội dung văn bản |
| date | created_at | Phân tích múi giờ và chuyển UTC |
| target | ground_truth_label | 0=negative, 2=neutral, 4=positive |
| Không có | platform | Gán "twitter" |
| Không có | content_type | Gán "post" |
| Không có | language | Gán "en" theo phạm vi dữ liệu |
| Không có | collected_at | Thời điểm pipeline tiếp nhận |
| Không có | engagement.likes | null |
| Không có | engagement.replies | null |
| Không có | engagement.shares | null |

Sentiment140 không có header trong file CSV gốc.

Thứ tự sáu trường:
target, ids, date, flag, user, text.

Tập Training chỉ có nhãn 0 và 4.
Tập Test có nhãn 0, 2 và 4.

Không được tự tạo nhãn neutral cho Training.


## 4. Quy tắc tạo event_id

### 4.1. Phương pháp triển khai thực tế

Đối với Sentiment140 Training, hệ thống tạo event_id
bằng cách kết hợp:

- Tiền tố nguồn dữ liệu: s140_train.
- ID tweet gốc: ids.
- Số thứ tự của bản ghi trong nhóm cùng ID: id_sequence.

Công thức:

event_id = "s140_train_" + ids + "_" + id_sequence

Ví dụ:

- s140_train_1467810369_1
- s140_train_1467810369_2
- s140_train_1467810672_1

### 4.2. Công cụ và phương pháp

Sử dụng Spark SQL Window Function:

- partitionBy("ids"): Nhóm các bản ghi cùng ID gốc.
- orderBy("target", "date", "flag", "user", "text"):
  Sắp xếp các bản ghi trong từng nhóm.
- row_number(): Đánh số thứ tự từ 1 trong mỗi nhóm.

Phương pháp này cho phép giữ lại các bản ghi có ID
gốc trùng nhau mà không tạo event_id trùng nhau.

### 4.3. Kết quả kiểm định

Trên Sentiment140 Training:

- Tổng bản ghi: 1.600.000.
- Event ID duy nhất: 1.600.000.
- Event ID trùng: 0.
- Event ID rỗng: 0.

Kết quả kiểm định sau khi xuất Parquet đạt yêu cầu.

### 4.4. Giới hạn của phương pháp

Nếu các bản ghi có cùng ID và cùng toàn bộ giá trị
dùng để sắp xếp, row_number() không bảo đảm thứ tự
gán số cho từng dòng vật lý qua các lần thực thi.

Do đó, phương pháp hiện tại bảo đảm tính duy nhất
trong kết quả đã kiểm định, nhưng chưa bảo đảm
truy vết chính xác về từng dòng CSV gốc.

Để bảo đảm truy vết theo dòng nguồn trong tương lai,
cần bổ sung vị trí dòng gốc hoặc một định danh nguồn
ổn định trong quá trình ingestion.

Không được xem id_sequence là số dòng CSV gốc.
```

Nhấn **Ctrl + S**.

## Bước 13.2. Tại sao cần ghi rõ giới hạn?

T giải thích ngắn gọn:

Giả sử trong CSV có hai dòng hoàn toàn giống nhau:

```text
ID: 123 | Text: Hello | Label: positive
ID: 123 | Text: Hello | Label: positive
```

Spark có thể tạo:

```text
s140_train_123_1
s140_train_123_2
```

Cả hai ID đều duy nhất. Nhưng vì hai dòng giống hệt nhau, Spark không có thông tin để biết dòng nào là dòng thứ nhất trong CSV gốc.

Vì vậy, ta cần phân biệt:

| Tiêu chí | Hiện trạng |
|---|---|
| ID duy nhất trong Parquet | Đã kiểm định PASS |
| Không làm mất bản ghi | Đã kiểm định đủ 1,6 triệu |
| Truy vết chính xác số dòng CSV gốc | Chưa hỗ trợ |
| Bảo đảm gán ID ổn định cho từng dòng vật lý | Chưa chứng minh |

Điều này không làm mất giá trị của kết quả Batch hiện tại. Nó chỉ xác định đúng phạm vi mà phương pháp đã chứng minh được.

---

## Bước 13.3. Kiểm tra tài liệu và trạng thái Git

Trong Terminal VS Code, chạy:

```powershell
Test-Path .\docs\w02_field_mapping.md
Test-Path .\docs\reports\w03_batch_benchmark.md
Test-Path .\docs\reports\w03_batch_read_benchmark.json
```

Mong đợi:

```text
True
True
True
```

Sau đó chạy:

```powershell
git status --short
```

Lệnh này giúp chúng ta xem những file đã thay đổi trước khi commit.

## Tiến độ Tuần 3

<box border radius="lg" padding={3} gap={2}>
  <row align="center" gap={2}>
    <icon name="check-circle" color="success"/>
    Xử lý 1.600.000 tweet bằng PySpark
  </row>
  <row align="center" gap={2}>
    <icon name="check-circle" color="success"/>
    Chuẩn hóa dữ liệu và xuất Parquet
  </row>
  <row align="center" gap={2}>
    <icon name="check-circle" color="success"/>
    Kiểm định chất lượng Parquet: 7/7 PASS
  </row>
  <row align="center" gap={2}>
    <icon name="check-circle" color="success"/>
    Benchmark: Parquet nhanh hơn khoảng 3,33 lần trong phép thử
  </row>
  <row align="center" gap={2}>
    <icon name="circle-dashed" color="secondary"/>
    Đồng bộ tài liệu với code
  </row>
  <row align="center" gap={2}>
    <icon name="circle" color="tertiary"/>
    Commit và push Tuần 3 lên GitHub
  </row>
</box>


## 5. Quy tắc xử lý thời gian

Twitter Airline:
- Đọc tweet_created kèm timezone offset.
- Chuyển thành ISO 8601 UTC.

Sentiment140:
- Đọc định dạng ngày giờ Twitter cũ.
- Nhận diện múi giờ PDT/PST theo dữ liệu thực tế.
- Chuyển chính xác sang UTC.
- Nếu không phân tích được, ghi nhận lỗi.

Không tự thay created_at bằng thời gian hiện tại.

collected_at là thời điểm pipeline tiếp nhận dữ liệu,
không phải thời gian tweet được đăng.

## 6. Quy tắc xử lý dữ liệu thiếu

- text rỗng: ghi nhận là bản ghi không hợp lệ
  cho phân tích cảm xúc.
- created_at không hợp lệ: ghi nhận lỗi; có thể
  để null nếu schema cho phép.
- likes/replies/shares không tồn tại: dùng null.
- Không tự thay null bằng 0 khi chưa có căn cứ.
- Nhãn không hợp lệ: không dùng bản ghi đó để
  huấn luyện mô hình có giám sát.

Không chỉnh sửa file dữ liệu gốc.

## 7. Quy tắc về nhãn cảm xúc

Phải phân biệt hai trường:

ground_truth_label:
- Nhãn có sẵn trong dataset.
- Phục vụ huấn luyện và đánh giá mô hình.

sentiment_label:
- Nhãn do mô hình Machine Learning dự đoán.
- Chỉ xuất hiện sau bước inference.

Không được sao chép ground_truth_label sang
sentiment_label rồi coi đó là kết quả dự đoán ML.

## 8. Quy tắc xử lý trùng lặp

Đối với Batch:
- Giữ nguyên dữ liệu gốc.
- Ghi nhận số bản ghi trùng.
- Cho phép tạo dữ liệu đã làm sạch riêng.

Đối với Machine Learning:
- Xử lý trùng lặp trước khi chia train/test.
- Xem xét loại bỏ nhóm cùng text nhưng khác nhãn.
- Tránh để nội dung giống nhau xuất hiện ở cả
  tập huấn luyện và kiểm thử.

Mọi thao tác loại dữ liệu phải có thống kê
số dòng trước và sau.

## 9. Đầu ra mong muốn

Dữ liệu chuẩn hóa cần có tối thiểu:
- event_id
- platform
- content_type
- text
- language
- created_at
- collected_at
- engagement

Các trường bổ sung cho dữ liệu lịch sử:
- source_record_id
- ground_truth_label

Khi tích hợp Machine Learning:
- sentiment_label
- sentiment_confidence
- model_version
- processed_at
- processing_mode

Các trường bổ sung phải được thống nhất trong
output contract trước khi tích hợp hai pipeline.

## 10. Phương pháp và lý do lựa chọn

Phương pháp: Schema Mapping và Data Standardization.

Lý do:
- Đồng nhất dữ liệu từ nhiều nguồn.
- Giảm phụ thuộc vào cấu trúc CSV gốc.
- Cho phép sử dụng cùng quy trình xử lý ở
  các bước Batch và Machine Learning.
- Hỗ trợ kiểm chứng Variety.
- Giúp truy vết các lỗi dữ liệu.

Phương án thay thế:
Xây dựng chương trình xử lý riêng cho từng dataset
mà không có schema chung.

Hạn chế của phương án thay thế:
- Khó tích hợp.
- Khó bảo trì.
- Dễ xuất hiện khác biệt về tên trường và kiểu dữ liệu.

## 11. Trạng thái

Đây là bản thiết kế mapping.

Chưa thực hiện chuyển đổi dữ liệu bằng PySpark.
Phần triển khai kỹ thuật sẽ được thực hiện ở Tuần 3.
