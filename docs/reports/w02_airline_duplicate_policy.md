
# W02 – Phương pháp xử lý dữ liệu trùng lặp

## 1. Kết quả khảo sát

Dataset Twitter US Airline Sentiment gồm 14.640 bản ghi.

Kết quả kiểm tra:
- 155 nhóm trùng ID.
- 155 dòng ID trùng vượt quá lần xuất hiện đầu tiên.
- 18 nhóm trùng ID nhưng khác nhãn.
- 187 nhóm trùng nội dung văn bản.
- 213 dòng trùng văn bản vượt quá lần xuất hiện đầu tiên.
- 25 nhóm trùng văn bản nhưng khác nhãn cảm xúc.

Các nhóm trùng ID và trùng văn bản có thể chồng lấn.

## 2. Vấn đề phát hiện

Dữ liệu tồn tại hiện tượng duplicate records và
conflicting labels.

Các bản ghi trùng nội dung có thể gây rò rỉ dữ liệu
nếu được phân chia giữa tập train và test.

Các bản ghi cùng nội dung nhưng khác nhãn tạo ra
sự không nhất quán trong dữ liệu huấn luyện.

## 3. Phương pháp xử lý đề xuất

### Đối với Batch Processing

Giữ nguyên dữ liệu gốc tại tầng Raw/Bronze.

Trong quá trình xử lý Batch, thống kê và ghi nhận
các bản ghi trùng lặp. Tạo dữ liệu đã chuẩn hóa
mà không thay đổi file gốc.

### Đối với Machine Learning

1. Kiểm tra các bản ghi thiếu nội dung hoặc nhãn.
2. Xác định các nhóm văn bản có nhãn mâu thuẫn.
3. Loại những nhóm văn bản có nhãn mâu thuẫn khỏi
   tập dữ liệu dùng để huấn luyện và đánh giá.
4. Với các nhóm văn bản trùng và cùng nhãn, chỉ
   giữ một bản ghi đại diện.
5. Chia dữ liệu train/validation/test sau khi xử lý
   trùng lặp.
6. Ghi nhận số bản ghi trước và sau khi làm sạch.

## 4. Lý do lựa chọn

Phương pháp giúp hạn chế data leakage, tránh tự
gán nhãn cho các trường hợp mâu thuẫn và cải thiện
tính nhất quán của tập dữ liệu huấn luyện.

Việc giữ nguyên dữ liệu gốc giúp kiểm tra và
tái thực hiện quy trình xử lý khi cần thiết.

## 5. Hạn chế

Việc loại bỏ dữ liệu trùng có thể làm giảm quy mô
tập huấn luyện hoặc thay đổi phân bố nhãn.

Các văn bản giống nhau cũng có thể mang cảm xúc
khác nhau tùy ngữ cảnh; việc loại bỏ các nhóm nhãn
mâu thuẫn là lựa chọn thận trọng cho mô hình chỉ
sử dụng nội dung text.

Phương pháp này chưa được áp dụng vào dữ liệu.
Kết quả làm sạch sẽ được ghi nhận ở giai đoạn
tiền xử lý và huấn luyện Machine Learning.
