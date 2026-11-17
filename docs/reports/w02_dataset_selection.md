
# W02 – Đánh giá và lựa chọn bộ dữ liệu

## 1. Mục tiêu
Lựa chọn dữ liệu phù hợp cho hai nhiệm vụ:
- Batch Processing và thực nghiệm Volume.
- Machine Learning phân loại ba nhãn cảm xúc.

## 2. Twitter US Airline Sentiment

- Số bản ghi: 14.640.
- Số cột: 15.
- Negative: 9.178 (62,69%).
- Neutral: 3.099 (21,17%).
- Positive: 2.363 (16,14%).
- Dòng ID trùng vượt lần đầu: 155.
- Dòng text trùng vượt lần đầu: 213.
- Không phát hiện text rỗng hoặc nhãn không hợp lệ.
- Giấy phép công bố: CC BY-NC-SA 4.0.
- Nguồn: https://www.kaggle.com/crowdflower/twitter-airline-sentiment

Quyết định: Chọn làm nguồn dữ liệu chính cho
mô hình Machine Learning ba nhãn.

Lý do: Có đủ Positive, Neutral và Negative.
Quy mô tương đối nhỏ, thuận tiện cho huấn luyện
baseline và kiểm tra kết quả.

Hạn chế: Nhãn mất cân bằng, có bản ghi trùng và
mâu thuẫn nhãn; nội dung chủ yếu thuộc ngành hàng không.

## 3. Sentiment140

### Training
- Số bản ghi: 1.600.000.
- Negative: 800.000.
- Positive: 800.000.
- Không có Neutral.
- Dòng ID trùng vượt lần đầu: 1.685.
- Dòng text trùng vượt lần đầu: 19.112.
- Không phát hiện dòng sai cấu trúc hoặc text rỗng.

### Test
- Số bản ghi: 498.
- Negative: 177.
- Neutral: 139.
- Positive: 182.

Nguồn:
https://huggingface.co/datasets/stanfordnlp/sentiment140

Giấy phép: Chưa xác định giấy phép nguồn mở
rõ ràng từ thẻ dữ liệu; cần tuân thủ điều khoản
sử dụng dữ liệu và tránh phân phối lại tweet thô
khi chưa xác minh quyền sử dụng.

Quyết định: Chọn Training để thử nghiệm
Batch Processing và Volume.

Lý do: Số lượng lớn, phù hợp để kiểm thử
đọc dữ liệu, chuẩn hóa, lọc, thống kê và lưu Parquet.

Hạn chế: Chỉ có hai nhãn trong Training;
không thể xem đây là dữ liệu huấn luyện ba nhãn.

## 4. Phương pháp lựa chọn

Sử dụng phương pháp so sánh đa tiêu chí:

1. Số lượng bản ghi.
2. Số lượng và phân bố nhãn.
3. Chất lượng dữ liệu.
4. Khả năng chuẩn hóa.
5. Sự phù hợp với nhiệm vụ.
6. Giấy phép và quyền sử dụng.

Không lựa chọn dataset chỉ dựa trên số dòng.

## 5. Các giới hạn cần lưu ý

- Hai nguồn khác nhau về miền dữ liệu.
- Dữ liệu trùng cần xử lý trước khi chia train/test.
- Kết quả timestamp mới được kiểm tra về định dạng.
- Chưa hoàn tất chuẩn hóa toàn bộ thời gian về UTC.
- Chưa kiểm chứng hoàn toàn các lỗi encoding.
- Chưa thực hiện Batch Processing chính thức.
- Chưa huấn luyện mô hình ML.

## 6. Kết luận

Twitter US Airline Sentiment được chọn cho
Machine Learning ba nhãn.

Sentiment140 Training được chọn cho Batch
Processing và thực nghiệm Volume.

Hai nguồn sẽ được chuẩn hóa về cùng data schema
trong các bước triển khai tiếp theo.
