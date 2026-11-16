
# Data Schema – Big Data Sentiment Pipeline

## 1. Mục đích

Thống nhất cấu trúc dữ liệu đầu vào cho toàn bộ hệ thống
thu thập, xử lý và phân tích cảm xúc mạng xã hội.

## 2. Schema Version

Version: 1.0

## 3. Required Fields

- event_id: string, định danh duy nhất
- platform: string, nguồn dữ liệu
- content_type: string, post hoặc comment
- text: string, nội dung văn bản
- language: string | null, mã ngôn ngữ
- created_at: ISO 8601 UTC string | null
- collected_at: ISO 8601 UTC string
- engagement: object

## 4. Engagement Fields

- likes: integer | null
- replies: integer | null
- shares: integer | null

Không tự điền 0 khi nguồn không cung cấp dữ liệu.

## 5. Sentiment Output

Các trường được bổ sung sau bước NLP:

- sentiment_label: positive | negative | neutral
- sentiment_confidence: float | null
- processed_at: ISO 8601 UTC string

## 6. Quy tắc chung

- Mỗi sự kiện phải có event_id duy nhất.
- Giữ nguyên nội dung văn bản gốc.
- Mọi thời điểm phải sử dụng UTC.
- Các trường không có dữ liệu được phép nhận null.
- Không tự ý thay đổi tên trường.
- Không đưa API key hoặc thông tin nhạy cảm vào JSON.
- Thay đổi schema phải được nhóm trưởng phê duyệt.

## 7. Phân công

- Crawler: Thu thập và chuẩn hóa dữ liệu đầu vào.
- NLP: Tiếp nhận text và bổ sung kết quả cảm xúc.
- Dashboard: Sử dụng dữ liệu đầu ra đã xử lý.
- Nhóm trưởng: Quản lý schema và tích hợp pipeline.
