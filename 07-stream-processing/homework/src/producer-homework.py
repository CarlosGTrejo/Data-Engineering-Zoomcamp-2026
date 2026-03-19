# import sys
import time

# from pathlib import Path
# sys.path.insert(0, str(Path(__file__).parent.parent))
import pandas as pd
from kafka import KafkaProducer
from models import Ride

# Download NYC yellow taxi trip data (first 1000 rows)
url = "https://d37ci6vzurychx.cloudfront.net/trip-data/green_tripdata_2025-10.parquet"
columns = [
    "PULocationID",
    "DOLocationID",
    "passenger_count",
    "trip_distance",
    "tip_amount",
    "total_amount",
    "lpep_pickup_datetime",
    "lpep_dropoff_datetime",
]

df = pd.read_parquet(url, columns=columns)


server = "localhost:9092"
topic_name = "green-trips"
producer = KafkaProducer(
    bootstrap_servers=[server],
    value_serializer=lambda ride_obj: ride_obj.to_json_bytes(),
)

row_count = 0
t0 = time.time()


for _, row in df.iterrows():
    ride = Ride.from_row(row)
    producer.send(topic_name, value=ride)
    row_count += 1
else:
    print(f"Sent {row_count} rows")

producer.flush()

t1 = time.time()
print(f"took {(t1 - t0):.2f} seconds")
