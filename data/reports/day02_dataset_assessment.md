# BÁO CÁO DAY 2 – KHẢO SÁT VÀ ĐÁNH GIÁ BỘ DỮ LIỆU

## 1. Tổng quan bộ dữ liệu

Trong ngày 2, nhóm đã tiến hành thu thập, đọc và phân tích sơ bộ ba file dữ liệu phục vụ bài toán phân tích cảm xúc (Sentiment Analysis).

Kết quả thống kê:

| Bộ dữ liệu | Số bản ghi | Dung lượng | Số lớp nhãn |
|---|---:|---:|---:|
| Twitter US Airline Sentiment | 14.640 | 3,263 MB | 3 |
| Sentiment140 Training | 1.600.000 | 227,741 MB | 2 |
| Sentiment140 Test | 498 | 0,071 MB | 3 |
| **Tổng cộng** | **1.615.138** | **231,075 MB** | — |

Cả ba file đều được đọc thành công. Không phát hiện dòng sai cấu trúc, nội dung văn bản rỗng, nhãn bị thiếu hoặc nhãn không hợp lệ.

### 1.1. Cấu trúc các bộ dữ liệu

**Twitter US Airline Sentiment**

Bộ dữ liệu có 15 cột:

- `tweet_id`: Mã định danh bài đăng.
- `airline_sentiment`: Nhãn cảm xúc.
- `airline_sentiment_confidence`: Độ tin cậy của nhãn.
- `negativereason`: Lý do đánh giá tiêu cực.
- `negativereason_confidence`: Độ tin cậy của lý do tiêu cực.
- `airline`: Hãng hàng không được đề cập.
- `airline_sentiment_gold`: Nhãn cảm xúc được xác minh.
- `name`: Tên tài khoản.
- `negativereason_gold`: Lý do tiêu cực được xác minh.
- `retweet_count`: Số lượt chia sẻ lại.
- `text`: Nội dung bài đăng.
- `tweet_coord`: Tọa độ bài đăng.
- `tweet_created`: Thời gian đăng bài.
- `tweet_location`: Vị trí người đăng.
- `user_timezone`: Múi giờ người đăng.

**Sentiment140 Training và Test**

Hai file có cùng cấu trúc gồm 6 trường:

| Tên trường | Ý nghĩa |
|---|---|
| `target` | Nhãn cảm xúc |
| `ids` | Mã định danh bài đăng |
| `date` | Thời gian đăng bài |
| `flag` | Trường thông tin bổ sung |
| `user` | Tên tài khoản |
| `text` | Nội dung bài đăng |

Các file Sentiment140 không có dòng tiêu đề. Tên cột được xác định dựa trên vị trí các trường trong bản ghi.

---

## 2. Phân tích phân bố nhãn cảm xúc

Để thống nhất cách biểu diễn nhãn giữa các bộ dữ liệu, nhóm sử dụng quy ước:

- Negative: Tiêu cực.
- Neutral: Trung tính.
- Positive: Tích cực.

### 2.1. Twitter US Airline Sentiment

| Nhãn | Số lượng | Tỷ lệ |
|---|---:|---:|
| Tiêu cực (Negative) | 9.178 | 62,69% |
| Trung tính (Neutral) | 3.099 | 21,17% |
| Tích cực (Positive) | 2.363 | 16,14% |
| **Tổng** | **14.640** | **100%** |

Nhận xét:

- Bộ dữ liệu có đầy đủ ba lớp cảm xúc.
- Nhãn Tiêu cực chiếm tỷ lệ cao nhất, đạt 62,69%.
- Nhãn Tích cực chỉ chiếm 16,14%.
- Phân bố nhãn không đồng đều, thể hiện tình trạng mất cân bằng dữ liệu.

Vì vậy, khi huấn luyện và đánh giá mô hình, cần quan tâm đến các chỉ số như Precision, Recall và Macro-F1, thay vì chỉ sử dụng Accuracy.

### 2.2. Sentiment140 Training

| Nhãn gốc | Nhãn chuẩn hóa | Số lượng | Tỷ lệ |
|---|---|---:|---:|
| 0 | Tiêu cực | 800.000 | 50% |
| 4 | Tích cực | 800.000 | 50% |
| **Tổng** | — | **1.600.000** | **100%** |

Nhận xét:

- Bộ Training chỉ có hai lớp cảm xúc: Tiêu cực và Tích cực.
- Không có nhãn Trung tính.
- Hai lớp có số lượng bằng nhau, do đó phân bố nhãn cân bằng.

### 2.3. Sentiment140 Test

| Nhãn gốc | Nhãn chuẩn hóa | Số lượng | Tỷ lệ |
|---|---|---:|---:|
| 0 | Tiêu cực | 177 | 35,54% |
| 2 | Trung tính | 139 | 27,91% |
| 4 | Tích cực | 182 | 36,55% |
| **Tổng** | — | **498** | **100%** |

Nhận xét:

- Bộ Test có đầy đủ ba lớp cảm xúc.
- Phân bố giữa ba lớp tương đối đồng đều.
- Có sự khác biệt về không gian nhãn giữa Training và Test: Training chỉ có hai lớp, trong khi Test có ba lớp.

**Lưu ý:** Không được tự bổ sung nhãn Trung tính vào Training. Nhóm cần thống nhất với Member C về phạm vi bài toán và phương pháp đánh giá phù hợp với sự khác biệt này.

---

## 3. Đánh giá chất lượng dữ liệu

### 3.1. Kiểm tra tính hợp lệ của bản ghi

| Tiêu chí | Twitter Airline | S140 Training | S140 Test |
|---|---:|---:|---:|
| Số dòng sai cấu trúc | 0 | 0 | 0 |
| Text rỗng | 0 | 0 | 0 |
| Nhãn bị thiếu | 0 | 0 | 0 |
| Nhãn không hợp lệ | 0 | 0 | 0 |
| ID trùng lặp (số dòng lặp) | 155 | 1.685 | 0 |
| Text trùng lặp (số dòng lặp) | 213 | 18.534 | 0 |

Nhận xét:

- Cả ba file đều có cấu trúc dữ liệu hợp lệ theo kết quả kiểm tra.
- Không phát hiện bản ghi thiếu nội dung văn bản hoặc nhãn cảm xúc.
- Sentiment140 Training có 18.534 dòng văn bản trùng lặp.
- Twitter US Airline Sentiment có 213 dòng văn bản trùng lặp và 155 dòng ID trùng lặp.

Các bản ghi trùng lặp cần được xem xét trước khi chia tập huấn luyện và kiểm thử nhằm hạn chế hiện tượng rò rỉ dữ liệu (Data Leakage).

### 3.2. Kiểm tra thời gian

| Bộ dữ liệu | Số timestamp không đọc được |
|---|---:|
| Twitter US Airline Sentiment | 0 |
| Sentiment140 Training | 1.600.000 |
| Sentiment140 Test | 498 |

Đối với Sentiment140, toàn bộ trường thời gian hiện chưa được hàm phân tích nhận diện đúng định dạng.

Đây có thể là vấn đề trong cách xử lý định dạng ngày giờ, không đồng nghĩa với việc toàn bộ dữ liệu thời gian bị hỏng. Cần kiểm tra lại định dạng timestamp và sửa hàm phân tích trước khi đưa ra kết luận cuối cùng.

### 3.3. Kiểm tra Encoding

| Bộ dữ liệu | Số ký tự thay thế trong trường text |
|---|---:|
| Twitter US Airline Sentiment | 630 |
| Sentiment140 Training | 0 |
| Sentiment140 Test | 0 |

Twitter US Airline Sentiment xuất hiện 630 ký tự thay thế trong quá trình giải mã văn bản.

Một số bản ghi còn có hiện tượng hiển thị sai ký tự (mojibake), đặc biệt đối với dấu ngoặc kép, dấu câu và emoji.

Cần kiểm tra lại encoding của file gốc và lựa chọn phương pháp xử lý phù hợp. Không nên coi những ký tự bị thay thế là dữ liệu văn bản nguyên bản.

---

## 4. Khảo sát đặc điểm nội dung văn bản

Qua việc kiểm tra các bản ghi mẫu, nhóm nhận thấy dữ liệu có nhiều đặc điểm đặc trưng của nội dung trên mạng xã hội:

1. **Mention:** Xuất hiện tên tài khoản được đề cập, ví dụ `@VirginAmerica`, `@switchfoot`.
2. **Hashtag:** Có các từ khóa bắt đầu bằng ký tự `#`, ví dụ `#fabulous`, `#kindle2`.
3. **URL:** Nhiều bài đăng chứa liên kết đến các trang web.
4. **HTML Entity:** Xuất hiện các chuỗi như `&amp;`, `&lt;3`.
5. **Dấu câu và biểu cảm:** Có nhiều dấu chấm than, dấu ba chấm, ký hiệu cảm xúc và emoji.
6. **Ngôn ngữ không trang trọng:** Xuất hiện từ viết tắt, cách viết kéo dài ký tự và cách diễn đạt đời thường.
7. **Phủ định:** Một số bài đăng chứa các từ như `not`, `no`, `didn't`, có thể ảnh hưởng đáng kể đến kết quả phân loại cảm xúc.

Những đặc điểm này cần được xem xét trong bước tiền xử lý văn bản. Đặc biệt, không nên loại bỏ toàn bộ từ phủ định vì chúng có thể làm thay đổi ý nghĩa cảm xúc của câu.

---

## 5. Các vấn đề cần lưu ý khi tiền xử lý

Từ kết quả khảo sát, nhóm đề xuất một số hướng xử lý:

- Chuẩn hóa nhãn cảm xúc về ba giá trị Negative, Neutral và Positive khi phù hợp với bài toán.
- Giữ lại bản dữ liệu gốc để có thể đối chiếu và khôi phục khi cần thiết.
- Kiểm tra và xử lý các bản ghi trùng lặp trước khi chia tập dữ liệu.
- Xử lý HTML Entity, URL, mention và hashtag theo quy tắc thống nhất.
- Kiểm tra encoding và các ký tự lỗi trong Twitter Airline.
- Giữ lại những từ phủ định quan trọng trong quá trình làm sạch văn bản.
- Không sử dụng các trường thông tin cá nhân hoặc vị trí không cần thiết như `name`, `tweet_location`, `user_timezone` làm đầu vào mô hình.
- Cân nhắc sử dụng Macro-F1 để đánh giá mô hình trong trường hợp dữ liệu mất cân bằng.

---

## 6. Những điểm khác biệt giữa các bộ dữ liệu

| Tiêu chí | Twitter Airline | Sentiment140 Training | Sentiment140 Test |
|---|---|---|---|
| Miền dữ liệu | Hàng không | Twitter tổng quát | Twitter tổng quát |
| Số bản ghi | 14.640 | 1.600.000 | 498 |
| Số lớp | 3 | 2 | 3 |
| Nhãn Trung tính | Có | Không | Có |
| Mức độ cân bằng | Mất cân bằng | Cân bằng | Tương đối cân bằng |

Hai bộ dữ liệu có sự khác biệt về lĩnh vực nội dung, số lượng bản ghi và phân bố nhãn. Do đó, khi kết hợp hoặc đánh giá chéo giữa các bộ dữ liệu, cần xem xét vấn đề dịch chuyển miền dữ liệu (Domain Shift).

---

## 7. Kết luận

Trong Day 2, nhóm đã hoàn thành việc đọc và khảo sát sơ bộ ba file dữ liệu với tổng cộng 1.615.138 bản ghi và dung lượng khoảng 231,075 MB.

Kết quả cho thấy:

- Các file đều có thể đọc và phân tích được.
- Không có bản ghi sai cấu trúc, text rỗng hoặc nhãn bị thiếu.
- Twitter Airline có ba lớp cảm xúc nhưng mất cân bằng nhãn.
- Sentiment140 Training có hai lớp cân bằng, trong khi Test có ba lớp.
- Một số vấn đề về bản ghi trùng lặp, encoding và timestamp cần được xử lý trước khi huấn luyện mô hình.

Nhìn chung, các bộ dữ liệu đáp ứng yêu cầu khảo sát ban đầu. Tuy nhiên, nhóm cần thống nhất cách chuẩn hóa nhãn, xử lý dữ liệu trùng lặp và lựa chọn chiến lược đánh giá mô hình trước khi chuyển sang các bước tiếp theo.



### 4.1. Kết quả khảo sát 20 mẫu văn bản bất thường

Nhóm đã sử dụng script `inspect_anomalies.py` để quét toàn bộ ba bộ dữ liệu, với tổng cộng 1.615.138 bản ghi.

Trong lần khảo sát hiện tại, script tự động trích xuất được 15 mẫu văn bản thuộc các nhóm đặc điểm sau:

| Nhóm bất thường | Số mẫu | Đặc điểm quan sát |
|---|---:|---|
| Mention | 2 | Xuất hiện tên tài khoản được nhắc đến |
| Hashtag | 2 | Có từ khóa bắt đầu bằng dấu `#` |
| URL | 1 | Chứa đường dẫn đến trang web |
| HTML Entity | 2 | Có các chuỗi như `&amp;`, `&lt;3` |
| Từ phủ định | 2 | Có các từ như `didn't` |
| Từ viết tắt | 2 | Có cách viết không trang trọng như `ur`, `thx` |
| Ký tự thay thế encoding | 2 | Có dấu hiệu văn bản bị lỗi mã hóa |
| Ký tự Unicode | 1 | Có ký tự ngoài bảng ASCII |
| Xuống dòng | 1 | Có nội dung cần chuẩn hóa khoảng trắng |

**Nhận xét:**

- Nội dung mạng xã hội có nhiều cách biểu đạt không chuẩn hóa, do đó cần xây dựng quy trình tiền xử lý phù hợp.
- Mention và URL có thể được thay thế bằng các token thống nhất để hạn chế nhiễu.
- Hashtag có thể chứa thông tin chủ đề và cảm xúc, vì vậy cần cân nhắc giữ lại phần nội dung.
- HTML Entity cần được giải mã trước khi đưa vào mô hình.
- Các từ phủ định cần được bảo toàn vì có ảnh hưởng trực tiếp đến ý nghĩa cảm xúc.
- Từ viết tắt cần được chuẩn hóa có chọn lọc, tránh làm thay đổi ý nghĩa gốc.
- Một số mẫu Twitter Airline xuất hiện hiện tượng mojibake, cho thấy cần kiểm tra encoding trước khi thực hiện làm sạch văn bản.
- Không nên xóa toàn bộ ký tự Unicode vì có thể làm mất emoji và các thông tin biểu cảm hữu ích.

**Hạn chế của lần khảo sát:**

Script hiện tại chỉ trích xuất được 15 mẫu, chưa đủ 20 mẫu theo mục tiêu khảo sát. Các mẫu cũng tập trung chủ yếu ở Twitter US Airline Sentiment do cách giới hạn số mẫu theo nhóm. Cần bổ sung mẫu từ Sentiment140 để bảo đảm tính đại diện giữa các bộ dữ liệu.

Các mẫu được chọn có mục đích khảo sát định tính, không được sử dụng để suy ra tỷ lệ xuất hiện của từng dạng bất thường trong toàn bộ dữ liệu.

### Bổ sung mẫu bất thường từ Sentiment140 Training

Để tránh việc các mẫu khảo sát chỉ tập trung vào bộ dữ liệu Twitter US Airline Sentiment, nhóm tiến hành lấy thêm 5 mẫu từ Sentiment140 Training.

Các đặc điểm ghi nhận:

- **Mention và URL:** xuất hiện tên tài khoản dạng `@USER` và đường dẫn URL.
- **Ngôn ngữ không trang trọng:** xuất hiện cách viết rút gọn, tiếng lóng và biểu cảm như `Awww`, `shoulda`, `;D`.
- **Từ phủ định:** xuất hiện các cấu trúc như `can't`, cần được giữ lại vì có ảnh hưởng trực tiếp đến sắc thái cảm xúc.
- **Dấu câu:** có dấu ba chấm và cách sử dụng dấu câu không theo chuẩn văn bản học thuật.
- **Hashtag:** xuất hiện hashtag như `#itm`, có thể mang thông tin về chủ đề hoặc ngữ cảnh.

Kết hợp với 15 mẫu khảo sát từ Twitter US Airline Sentiment, nhóm đã kiểm tra tổng cộng 20 mẫu bất thường từ hai nguồn dữ liệu. Các mẫu được lựa chọn theo quy tắc phát hiện tự động, không phải mẫu ngẫu nhiên đại diện thống kê cho toàn bộ dữ liệu.