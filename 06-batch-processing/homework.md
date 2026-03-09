# Module 6 Homework

In this homework we'll put what we learned about Spark in practice.

For this homework we will be using the Yellow 2025-11 data from the official website:

```bash
wget https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2025-11.parquet
```


## Question 1: Install Spark and PySpark

- Install Spark
  - `mise use spark`
  - `uv add pyspark`
- Run PySpark
- Create a local spark session
- Execute spark.version.

What's the output?

- `4.1.1`

> [!NOTE]
> To install PySpark follow this [guide](https://github.com/DataTalksClub/data-engineering-zoomcamp/blob/main/06-batch/setup/)


## Question 2: Yellow November 2025

Read the November 2025 Yellow into a Spark Dataframe.

Repartition the Dataframe to 4 partitions and save it to parquet.

What is the average size of the Parquet (ending with .parquet extension) Files that were created (in MB)? Select the answer which most closely matches.

```py
df = spark.read.parquet('yellow_taxi.parquet', header = True, inferSchema = True)
df = df.repartition(4)
df.write.parquet('yellow', 'overwrite')
```


- [ ] 6MB
- [X] 25MB
- [ ] 75MB
- [ ] 100MB


## Question 3: Count records

How many taxi trips were there on the 15th of November?

Consider only trips that started on the 15th of November.

```py
df.filter((df.tpep_pickup_datetime >= '2025-11-15') & (df.tpep_pickup_datetime < '2025-11-16')).count()
```

- [ ] 62,610
- [ ] 102,340
- [X] 162,604
- [ ] 225,768


## Question 4: Longest trip

What is the length of the longest trip in the dataset in hours?

```py
df.withColumn('trip_duration', (F.unix_timestamp(df.tpep_dropoff_datetime) - F.unix_timestamp(df.tpep_pickup_datetime)) / 3600).agg({'trip_duration': 'max'}).show()
```

- [ ] 22.7
- [ ] 58.2
- [X] 90.6
- [ ] 134.5


## Question 5: User Interface

Spark's User Interface which shows the application's dashboard runs on which local port?

- [ ] 80
- [ ] 443
- [X] 4040
- [ ] 8080



## Question 6: Least frequent pickup location zone

Load the zone lookup data into a temp view in Spark:

```bash
wget https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv
```

Using the zone lookup data and the Yellow November 2025 data, what is the name of the LEAST frequent pickup location Zone?

```py
zone = spark.read.csv('zone.csv', header = True, inferSchema = True)
merged = df.join(zone, zone.LocationID == df.PULocationID, 'left').\
                withColumnRenamed('Zone', 'pickup_zone').drop('Borough', 'service_zone', 'LocationID')
merged.groupby('pickup_zone').count().sort('count', ascending = True).head(8)
```

- [X] Governor's Island/Ellis Island/Liberty Island
- [X] Arden Heights
- [ ] Rikers Island
- [ ] Jamaica Bay

If multiple answers are correct, select any