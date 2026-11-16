
import json
import uuid
from datetime import datetime, timezone

from kafka import KafkaProducer, KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import TopicAlreadyExistsError

KAFKA_SERVER = "localhost:9092"
TOPIC = "social_events_v1"


def utc_now():
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


# 1. Tao Kafka topic rieng cho schema moi
admin = KafkaAdminClient(
    bootstrap_servers=KAFKA_SERVER
)

try:
    admin.create_topics([
        NewTopic(
            name=TOPIC,
            num_partitions=3,
            replication_factor=1
        )
    ])
    print(f"Da tao topic: {TOPIC}")

except TopicAlreadyExistsError:
    print(f"Topic {TOPIC} da ton tai")

finally:
    admin.close()


# 2. Ket noi Kafka Producer
producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVER,
    value_serializer=lambda v: json.dumps(
        v, ensure_ascii=False
    ).encode("utf-8"),
    acks="all",
    retries=3
)


# 3. Du lieu gia lap de kiem thu
samples = [
    "The service was excellent!",
    "I am disappointed with the delay.",
    "The announcement is available online."
]


# 4. Tao su kien theo Data Schema v1.0
for text in samples:
    now = utc_now()

    event = {
        "event_id": f"demo_{uuid.uuid4().hex}",
        "platform": "simulated_reddit",
        "content_type": "comment",
        "text": text,
        "language": "en",
        "created_at": now,
        "collected_at": now,
        "engagement": {
            "likes": None,
            "replies": None,
            "shares": None
        }
    }

    result = producer.send(
        TOPIC, value=event
    ).get(timeout=10)

    print(
        f"Da gui: {event['event_id']} "
        f"| partition={result.partition} "
        f"| offset={result.offset}"
    )


producer.flush()
producer.close()

print("Hoan tat gui du lieu JSON v2!")
