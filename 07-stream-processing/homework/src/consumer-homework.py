from kafka import KafkaConsumer
from models import Ride

server = "localhost:9092"
topic_name = "green-trips"

consumer = KafkaConsumer(
    topic_name,
    bootstrap_servers=[server],
    auto_offset_reset="earliest",
    group_id="rides-console",
    value_deserializer=Ride.from_bytes,
)

print(f"(i) Listening to {topic_name}...")

count_trips_gt_5km = 0
for message in consumer:
    ride = message.value
    if ride.trip_distance > 5.0:
        count_trips_gt_5km += 1
    print(f"Total trips with distance > 5 km: {count_trips_gt_5km}", end="\r")
else:
    print(f"Total trips with distance > 5 km: {count_trips_gt_5km}")

consumer.close()
