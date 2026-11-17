# API / Polling / Replay Plan

## 1. Mục tiêu

Thiết kế đầu vào dữ liệu cho Big Data Sentiment Pipeline theo hai chế độ:

- **Replay (ưu tiên cho kiểm thử và demo):** đọc lại dữ liệu đã lưu để có thể tái lập kết quả.
- **Polling API (mở rộng):** định kỳ lấy bài đăng công khai mới từ nguồn có API phù hợp.

Không coi API là điều kiện bắt buộc để chạy pipeline. Pipeline phải chạy được bằng dữ liệu replay khi API không khả dụng.

## 2. Nguồn dữ liệu

| Nguồn | Mục đích | Cách truy cập | Điều kiện / hạn chế |
|---|---|---|---|
| Airline Tweets (`Tweets.csv`) | Replay, kiểm thử dữ liệu có 3 lớp | File CSV đã thu thập | Cần ghi nhận nguồn gốc và điều khoản của bản dataset đang sử dụng |
| Sentiment140 | Replay và kiểm thử khối lượng lớn | File CSV đã thu thập | Train chủ yếu có nhãn 0/4; không tự tạo nhãn neutral |
| Bluesky public API | Polling thử nghiệm | API đọc công khai | Dữ liệu mới không có nhãn cảm xúc chuẩn; phải gắn nguồn và trạng thái nhãn riêng |
| Mastodon public timeline | Nguồn API dự phòng | API của từng instance | Một số instance tắt public preview; giới hạn và quyền truy cập phụ thuộc instance |

### Nguồn tham khảo chính thức

- Bluesky API reference: https://docs.bsky.app/docs/api/app-bsky-feed-get-feed
- Bluesky rate limits: https://bsky.network/docs/rate-limits/
- Mastodon public timeline: https://docs.joinmastodon.org/methods/timelines/
- Mastodon rate limits: https://docs.joinmastodon.org/api/rate-limits/
- Sentiment140 dataset card: https://huggingface.co/datasets/stanfordnlp/sentiment140

## 3. Phương án Replay — đường chạy mặc định

### 3.1. Input

- `data/raw/Tweets.csv`
- File train/test Sentiment140 đã được nhóm tải và lưu cục bộ.

Không tải lại dữ liệu ở mỗi lần chạy. Không đưa dữ liệu thô hoặc file Parquet lớn lên Git nếu repository không yêu cầu.

### 3.2. Quy trình

1. Đọc đường dẫn và cấu hình dataset từ config.
2. Kiểm tra file tồn tại, encoding, header và số cột.
3. Chuẩn hóa tên cột về schema chung.
4. Chuẩn hóa timestamp về UTC nếu có thể xác định timezone.
5. Giữ lại ID nguồn để phục vụ deduplication.
6. Ghi dữ liệu đã chuẩn hóa ra định dạng trung gian Parquet.
7. Chạy các bước xử lý sentiment và aggregation.
8. Ghi log số dòng đầu vào, số dòng hợp lệ, số dòng bị loại và lý do.

### 3.3. Tính tái lập

Mỗi lần replay cần ghi nhận:

- Tên dataset và phiên bản/file nguồn.
- Thời điểm chạy.
- Số dòng đầu vào và đầu ra.
- Cấu hình chuẩn hóa.
- Số dòng thiếu text, thiếu timestamp hoặc trùng ID.
- Đường dẫn output.

Cùng một input và cùng cấu hình phải tạo ra kết quả thống kê tương đương.

## 4. Phương án Polling API — thử nghiệm có điều kiện

### 4.1. Nguồn ưu tiên: Bluesky

Dùng public read API của Bluesky, bắt đầu bằng endpoint tìm kiếm bài đăng:

`GET https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts`

API public của Bluesky hỗ trợ các truy vấn đọc mà không cần xác thực trong phạm vi endpoint công khai. Cần kiểm tra schema và tham số endpoint tại tài liệu chính thức trước khi triển khai.

Phạm vi thử nghiệm:
- Chỉ lấy bài đăng công khai.
- Chỉ lấy một truy vấn nhỏ hoặc một nhóm từ khóa thử nghiệm.
- Giới hạn số bản ghi mỗi lần poll.
- Lưu raw response để có thể replay lại.
- Không thu thập DM hoặc dữ liệu riêng tư.

### 4.2. Chu kỳ polling đề xuất

Đây là cấu hình thử nghiệm ban đầu, không phải giới hạn chính thức của nhà cung cấp:

- Chu kỳ: 5 phút/lần.
- Mỗi lần: tối đa 100 bài đăng.
- Duy trì cursor hoặc mốc thời gian truy vấn gần nhất nếu endpoint hỗ trợ.
- Dùng URI/CID hoặc định danh ổn định của bài đăng để chống trùng.
- Lưu thời điểm poll và trạng thái thành công/thất bại.

Nếu nhận HTTP 429:
- Dừng polling tạm thời.
- Tôn trọng thông tin rate limit hoặc thời gian retry do server trả về.
- Không liên tục gửi lại request.

Nếu lỗi 5xx hoặc timeout:
- Retry có giới hạn với exponential backoff.
- Sau số lần retry tối đa, ghi lỗi và chuyển sang replay.

### 4.3. Chuẩn hóa bản ghi API

Ánh xạ dữ liệu API vào schema chung của nhóm:

| Trường chuẩn | Nguồn đề xuất |
|---|---|
| `record_id` | URI hoặc ID ổn định của bài đăng |
| `source` | `bluesky` |
| `text` | Nội dung bài đăng |
| `created_at` | Timestamp do nguồn cung cấp |
| `ingested_at` | Thời điểm pipeline lấy dữ liệu |
| `sentiment_label` | Để null nếu chưa được gán nhãn |
| `label_source` | `unlabeled`, `manual` hoặc tên phương pháp gán nhãn |

Tên trường cuối cùng phải được đồng bộ với `docs/data_schema.md`.

### 4.4. Lưu ý về nhãn

Bài đăng lấy từ API không mặc nhiên có nhãn sentiment đúng.

- Không tự gán nhãn thật dựa trên dự đoán của model.
- Nếu dùng model để dự đoán, lưu kết quả ở trường prediction riêng.
- Nếu cần đánh giá mô hình, phải có tập kiểm thử được gán nhãn thủ công hoặc nguồn nhãn đáng tin cậy.
- Không trộn dữ liệu chưa gán nhãn vào tập train có giám sát.

## 5. Phương án dự phòng: Mastodon hoặc Replay

### Dự phòng API

Mastodon có endpoint public timeline:

`GET /api/v1/timelines/public`

Tuy nhiên, public timeline có thể bị tắt ở một số instance. Vì vậy cần:
1. Chọn instance cho phép truy cập công khai.
2. Gửi request giới hạn nhỏ.
3. Kiểm tra HTTP status và response schema.
4. Đọc các header rate limit.
5. Nếu instance từ chối hoặc không ổn định, không cố vượt hạn chế; chuyển sang replay.

### Dự phòng chắc chắn

Nếu cả Bluesky và Mastodon không khả dụng:
- Chạy replay từ dataset cục bộ.
- Giữ nguyên các bước normalize, transform, aggregate và load.
- Ghi `source_mode=replay` trong log để phân biệt với dữ liệu API.

## 6. Tiêu chí nghiệm thu

| ID | Kiểm tra | PASS khi |
|---|---|---|
| API-01 | Kết nối Bluesky | Request thử nghiệm nhận response hợp lệ |
| API-02 | Parse dữ liệu | Bản ghi được ánh xạ đúng schema |
| API-03 | Deduplication | Hai bản ghi cùng ID không tạo thành hai bản ghi đầu ra |
| API-04 | Rate limit | HTTP 429 được xử lý có backoff, không spam request |
| API-05 | API unavailable | Pipeline chuyển sang replay mà không dừng toàn bộ |
| REP-01 | Replay | Đọc được dataset cục bộ và hoàn thành pipeline |
| REP-02 | Reproducibility | Chạy cùng input/config cho kết quả thống kê tương đương |
| REP-03 | Audit | Log được số dòng đọc, loại, trùng và ghi thành công |

## 7. Trạng thái triển khai

- Replay từ dataset cục bộ: có dữ liệu và các bước xử lý đã được chạy trong quá trình phát triển.
- Bluesky polling: thiết kế đề xuất, chưa đánh dấu PASS cho đến khi có log request thực tế.
- Mastodon fallback: phương án thiết kế, chưa đánh dấu PASS cho đến khi kiểm thử một instance cụ thể.

## 8. Giới hạn và tuân thủ

- Chỉ truy cập dữ liệu công khai theo điều khoản của nền tảng.
- Không tìm cách vượt rate limit, xác thực hoặc quyền truy cập.
- Không commit token, cookie, secret hoặc dữ liệu cá nhân không cần thiết.
- Kiểm tra điều khoản dataset trước khi phân phối lại dữ liệu.
- Khi API không cung cấp nhãn sentiment, phải coi nhãn là null thay vì tự suy diễn.
