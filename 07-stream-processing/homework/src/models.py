import json
from dataclasses import dataclass


@dataclass
class Ride:
    PULocationID: int
    DOLocationID: int
    trip_distance: float
    tip_amount: float  # Added so Question 6 works!
    total_amount: float
    lpep_pickup_datetime: str  # Changed to string
    lpep_dropoff_datetime: str  # Changed to string

    @classmethod
    def from_row(cls, row):
        return cls(
            PULocationID=int(row["PULocationID"]),
            DOLocationID=int(row["DOLocationID"]),
            trip_distance=float(row["trip_distance"]),
            tip_amount=float(row["tip_amount"]),
            total_amount=float(row["total_amount"]),
            # Format the datetime objects directly to the required string pattern
            lpep_pickup_datetime=row["lpep_pickup_datetime"].strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            lpep_dropoff_datetime=row["lpep_dropoff_datetime"].strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        )

    @classmethod
    def from_bytes(cls, data):
        json_str = data.decode("utf-8")
        ride_dict = json.loads(json_str)
        return cls(**ride_dict)

    def to_json(self):
        return json.dumps(
            {
                "PULocationID": self.PULocationID,
                "DOLocationID": self.DOLocationID,
                "trip_distance": self.trip_distance,
                "tip_amount": self.tip_amount,
                "total_amount": self.total_amount,
                "lpep_pickup_datetime": self.lpep_pickup_datetime,
                "lpep_dropoff_datetime": self.lpep_dropoff_datetime,
            }
        )

    def to_json_bytes(self):
        json_str = self.to_json()
        return json_str.encode("utf-8")
