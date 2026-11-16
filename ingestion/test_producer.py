from kafka import KafkaProducer
import json
import time

# Khởi tạo trạm phát kết nối đến Kafka qua cổng 9092
producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

topic_name = 'raw_text_data'

# Giả lập luồng dữ liệu (Streaming Data) sinh ra liên tục
sample_reviews = [
    {"id": 1, "text": "Sản phẩm dùng rất tốt, đáng tiền!", "platform": "shopee"},
    {"id": 2, "text": "Giao hàng quá chậm, dịch vụ tệ.", "platform": "facebook"},
    {"id": 3, "text": "Chất lượng bình thường, tạm chấp nhận được.", "platform": "tiki"}
]

print("Bắt đầu bơm dữ liệu vào Kafka...")

for review in sample_reviews:
    # Đẩy từng dòng dữ liệu vào đường ống
    producer.send(topic_name, review)
    print(f"Đã gửi: {review}")
    time.sleep(2) 

producer.flush()
print("Hoàn tất bơm dữ liệu!")