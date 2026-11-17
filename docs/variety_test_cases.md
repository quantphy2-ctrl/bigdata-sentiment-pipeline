# Variety Test Cases

## 1. Mục tiêu

Kiểm tra pipeline có thể tiếp nhận và xử lý các dạng dữ liệu đầu vào khác nhau mà không làm sai schema, mất dữ liệu hợp lệ hoặc tạo thống kê sai.

Các ca kiểm thử được chia thành:
- Kiểm thử schema và dữ liệu thiếu.
- Kiểm thử nội dung văn bản đa dạng.
- Kiểm thử timestamp và encoding.
- Kiểm thử duplicate và dữ liệu nhiễu.
- Kiểm thử nhãn sentiment.
- Kiểm thử khối lượng và khả năng replay.

## 2. Test cases

| ID | Nhóm | Input / tình huống | Kết quả mong đợi | PASS khi | FAIL khi |
|---|---|---|---|---|---|
| VAR-01 | Văn bản thường | `I love this product` | Đọc và chuẩn hóa thành công | Text được giữ nguyên nội dung | Lỗi parse hoặc text bị mất |
| VAR-02 | Cảm xúc tiêu cực | `This is terrible` | Bản ghi được xử lý bình thường | Không bị loại chỉ vì nội dung tiêu cực | Pipeline loại nhầm bản ghi |
| VAR-03 | Cảm xúc trung tính | `The meeting starts at 9 AM` | Bản ghi được xử lý bình thường | Không tự ép thành positive/negative ở bước ingestion | Tự gán nhãn khi không có nhãn nguồn |
| VAR-04 | Phủ định | `I do not like this` | Giữ nguyên từ phủ định | Text không bị xóa từ `not` | Normalizer làm mất từ phủ định |
| VAR-05 | Emoji | `Great work 😊` | Giữ được Unicode/emoji | Đọc và ghi lại không lỗi encoding | Ký tự bị thay bằng `?` hoặc lỗi decode |
| VAR-06 | Mention/URL | `@user check https://example.com` | Xử lý được mention và URL | Không lỗi parse; áp dụng đúng quy tắc chuẩn hóa | Cắt sai toàn bộ nội dung |
| VAR-07 | Nội dung rỗng | Text là `null` hoặc chuỗi rỗng | Đánh dấu invalid hoặc đưa vào nhóm bị loại | Có log số dòng và lý do loại | Lỗi toàn bộ job hoặc âm thầm bỏ qua |
| VAR-08 | ID trùng | Hai bản ghi cùng `record_id` | Deduplicate theo quy tắc đã chọn | Chỉ còn một bản ghi theo khóa duy nhất | Đếm trùng thành hai bản ghi |
| VAR-09 | Timestamp ISO | `2026-11-17T09:30:00Z` | Parse thành timestamp UTC | Giá trị thời gian hợp lệ | Parse sai hoặc đổi lệch thời gian |
| VAR-10 | Timestamp sai | `not-a-date` | Đánh dấu timestamp invalid/null theo schema | Job tiếp tục và ghi log | Job crash hoặc tự tạo timestamp giả |
| VAR-11 | Encoding Latin-1 | Dữ liệu Sentiment140 | Đọc đúng encoding nguồn | Không lỗi decode và không hỏng text | UnicodeDecodeError hoặc mojibake |
| VAR-12 | Encoding Windows-1252 | Dữ liệu Airline Tweets | Đọc đúng encoding nguồn | Đọc được các ký tự đặc biệt | Lỗi decode hoặc mất ký tự |
| VAR-13 | Nhãn không hợp lệ | Label ngoài tập nhãn cho phép | Đánh dấu invalid | Có log hoặc quarantine bản ghi | Âm thầm đổi nhãn sang lớp khác |
| VAR-14 | Nhãn thiếu | API record không có sentiment label | Giữ `sentiment_label=null` | Bản ghi vẫn được ingest, không đưa nhầm vào supervised training | Tự gán nhãn thật |
| VAR-15 | Nội dung rất dài | Text dài hơn các mẫu thông thường | Xử lý theo giới hạn cấu hình | Không crash; có log nếu vượt giới hạn | Treo job hoặc cắt dữ liệu không kiểm soát |
| VAR-16 | Nội dung đa ngôn ngữ | Tiếng Việt có dấu, tiếng Anh, ký tự Unicode | Đọc và lưu đúng | Không lỗi encoding | Mất dấu hoặc lỗi ghi file |
| VAR-17 | Dữ liệu rỗng toàn file | CSV chỉ có header | Báo không có record hợp lệ | Job kết thúc có thông báo rõ ràng | Tạo thống kê giả hoặc crash không kiểm soát |
| VAR-18 | File thiếu cột | CSV thiếu cột text bắt buộc | Báo schema invalid | Có thông báo tên cột thiếu | Tiếp tục xử lý với dữ liệu sai schema |

## 3. Kiểm thử nhãn và thống kê

### Quy tắc nhãn

- Airline Tweets: kiểm tra các giá trị nhãn theo mapping đã khai báo trong cấu hình.
- Sentiment140 train: `0` là negative, `4` là positive; không tự thêm neutral vào train.
- Sentiment140 test: có thể chứa `0`, `2`, `4`; cần giữ đúng mapping.
- Dữ liệu API chưa gán nhãn: `sentiment_label=null`.

### Tiêu chí

1. Tổng số record theo nhãn phải bằng tổng record có nhãn hợp lệ.
2. Record không có nhãn không được cộng vào phân phối sentiment.
3. Nhãn ngoài miền cho phép phải được báo lỗi hoặc đưa vào quarantine.
4. Không tự chuyển đổi nhãn thiếu thành neutral.

## 4. Kiểm thử khối lượng

| ID | Quy mô | Mục tiêu | PASS khi |
|---|---:|---|---|
| VOL-01 | 100 records | Smoke test | Pipeline chạy hết các bước |
| VOL-02 | 10.000 records | Kiểm tra batch | Không mất record ngoài các trường hợp bị loại có log |
| VOL-03 | Dataset Airline Tweets | Kiểm tra dataset thực tế | Tổng số đọc/loại/ghi được đối soát |
| VOL-04 | Sentiment140 train + test | Kiểm tra dữ liệu lớn | Pipeline hoàn thành và thống kê khớp số dòng đầu vào đã xác minh |

## 5. Quy tắc kết luận

- **PASS:** kết quả thực tế khớp toàn bộ tiêu chí của test case.
- **FAIL:** kết quả thực tế vi phạm tiêu chí hoặc làm pipeline dừng ngoài dự kiến.
- **NOT RUN:** chưa chạy test; không được ghi thành PASS.
- **BLOCKED:** chưa thể chạy vì thiếu dữ liệu, quyền truy cập hoặc cấu hình.

## 6. Test execution log

| Test ID | Trạng thái | Bằng chứng |
|---|---|---|
| VAR-01 đến VAR-18 | NOT RUN / cập nhật sau khi chạy | Ghi tên log hoặc output |
| VOL-01 đến VOL-04 | NOT RUN / cập nhật sau khi chạy | Ghi tên log hoặc output |

Không đánh dấu PASS chỉ vì đã viết test case. Chỉ cập nhật trạng thái sau khi chạy thực tế.
