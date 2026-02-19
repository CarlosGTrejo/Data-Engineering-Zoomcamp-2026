/* @bruin

# Docs:
# - Materialization: https://getbruin.com/docs/bruin/assets/materialization
# - Quality checks (built-ins): https://getbruin.com/docs/bruin/quality/available_checks
# - Custom checks: https://getbruin.com/docs/bruin/quality/custom

# TODO: Set the asset name (recommended: staging.trips).
name: staging.trips
# TODO: Set platform type.
# Docs: https://getbruin.com/docs/bruin/assets/sql
# suggested type: duckdb.sql
type: duckdb.sql

# TODO: Declare dependencies so `bruin run ... --downstream` and lineage work.
# Examples:
# depends:
#   - ingestion.trips
#   - ingestion.payment_lookup
depends:
  - ingestion.trips
  - ingestion.payment_lookup

# TODO: Choose time-based incremental processing if the dataset is naturally time-windowed.
# - This module expects you to use `time_interval` to reprocess only the requested window.
materialization:
  # What is materialization?
  # Materialization tells Bruin how to turn your SELECT query into a persisted dataset.
  # Docs: https://getbruin.com/docs/bruin/assets/materialization
  #
  # Materialization "type":
  # - table: persisted table
  # - view: persisted view (if the platform supports it)
  type: table
  # TODO: set a materialization strategy.
  # Docs: https://getbruin.com/docs/bruin/assets/materialization
  # suggested strategy: time_interval
  #
  # Incremental strategies (what does "incremental" mean?):
  # Incremental means you update only part of the destination instead of rebuilding everything every run.
  # In Bruin, this is controlled by `strategy` plus keys like `incremental_key` and `time_granularity`.
  #
  # Common strategies you can choose from (see docs for full list):
  # - create+replace (full rebuild)
  # - truncate+insert (full refresh without drop/create)
  # - append (insert new rows only)
  # - delete+insert (refresh partitions based on incremental_key values)
  # - merge (upsert based on primary key)
  # - time_interval (refresh rows within a time window)
  strategy: time_interval
  incremental_key: pickup_datetime
  time_granularity: timestamp

columns:
  - name: trip_id
    type: string
    description: Deterministic surrogate key for a deduplicated trip row.
    primary_key: true
    nullable: false
    checks:
      - name: not_null
      - name: unique
  - name: taxi_type
    type: string
    description: Taxi type derived from source files (yellow/green).
    nullable: false
    checks:
      - name: not_null
  - name: pickup_datetime
    type: timestamp
    description: Normalized trip pickup timestamp.
    nullable: false
    checks:
      - name: not_null
  - name: dropoff_datetime
    type: timestamp
    description: Normalized trip dropoff timestamp.
    nullable: false
    checks:
      - name: not_null
  - name: pickup_location_id
    type: integer
    description: TLC location ID where the trip started.
    nullable: false
    checks:
      - name: not_null
  - name: dropoff_location_id
    type: integer
    description: TLC location ID where the trip ended.
    nullable: false
    checks:
      - name: not_null
  - name: payment_type_id
    type: integer
    description: Raw payment type identifier from trip data.
  - name: payment_type_name
    type: string
    description: Human-readable payment type from lookup table.
  - name: passenger_count
    type: integer
    description: Passenger count normalized to integer.
    checks:
      - name: non_negative
  - name: trip_distance
    type: double
    description: Trip distance in miles.
    checks:
      - name: non_negative
  - name: fare_amount
    type: double
    description: Base fare amount.
    checks:
      - name: non_negative
  - name: tip_amount
    type: double
    description: Tip amount paid for the trip.
    checks:
      - name: non_negative
  - name: total_amount
    type: double
    description: Total charged amount for the trip.
    checks:
      - name: non_negative
  - name: source_month
    type: string
    description: Source file month in YYYY-MM format.
  - name: source_url
    type: string
    description: Source parquet URL.
  - name: extracted_at
    type: timestamp
    description: UTC timestamp when the source file was extracted.

# TODO: Add one custom check that validates a staging invariant (uniqueness, ranges, etc.)
# Docs: https://getbruin.com/docs/bruin/quality/custom
custom_checks:
  - name: row_count_positive
    description: Ensure the staging table is not empty
    query: SELECT COUNT(*) > 0 FROM staging.trips
    value: 1
  - name: trip_id_unique
    description: Ensure deduplication produced unique trip IDs
    query: SELECT COUNT(*) = COUNT(DISTINCT trip_id) FROM staging.trips
    value: 1

@bruin */

-- TODO: Write the staging SELECT query.
--
-- Purpose of staging:
-- - Clean and normalize schema from ingestion
-- - Deduplicate records (important if ingestion uses append strategy)
-- - Enrich with lookup tables (JOINs)
-- - Filter invalid rows (null PKs, negative values, etc.)
--
-- Why filter by {{ start_datetime }} / {{ end_datetime }}?
-- When using `time_interval` strategy, Bruin:
--   1. DELETES rows where `incremental_key` falls within the run's time window
--   2. INSERTS the result of your query
-- Therefore, your query MUST filter to the same time window so only that subset is inserted.
-- If you don't filter, you'll insert ALL data but only delete the window's data = duplicates.

WITH base AS (
  SELECT
    taxi_type,
    lpep_pickup_datetime AS pickup_datetime,
    lpep_dropoff_datetime AS dropoff_datetime,
    CAST(pu_location_id AS INTEGER) AS pickup_location_id,
    CAST(do_location_id AS INTEGER) AS dropoff_location_id,
    CAST(payment_type AS INTEGER) AS payment_type_id,
    TRY_CAST(passenger_count AS INTEGER) AS passenger_count,
    TRY_CAST(trip_distance AS DOUBLE) AS trip_distance,
    TRY_CAST(fare_amount AS DOUBLE) AS fare_amount,
    TRY_CAST(tip_amount AS DOUBLE) AS tip_amount,
    TRY_CAST(total_amount AS DOUBLE) AS total_amount,
    source_month,
    source_url,
    extracted_at
  FROM ingestion.trips
  WHERE lpep_pickup_datetime >= TIMESTAMP '{{ start_datetime }}'
    AND lpep_pickup_datetime < TIMESTAMP '{{ end_datetime }}'
),
filtered AS (
  SELECT *
  FROM base
  WHERE pickup_datetime IS NOT NULL
    AND dropoff_datetime IS NOT NULL
    AND pickup_location_id IS NOT NULL
    AND dropoff_location_id IS NOT NULL
    AND pickup_datetime <= dropoff_datetime
    AND COALESCE(passenger_count, 0) >= 0
    AND COALESCE(trip_distance, 0) >= 0
    AND COALESCE(fare_amount, 0) >= 0
    AND COALESCE(tip_amount, 0) >= 0
    AND COALESCE(total_amount, 0) >= 0
),
deduplicated AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY
        taxi_type,
        pickup_datetime,
        dropoff_datetime,
        pickup_location_id,
        dropoff_location_id,
        COALESCE(payment_type_id, -1),
        COALESCE(trip_distance, -1),
        COALESCE(total_amount, -1)
      ORDER BY extracted_at DESC, source_url DESC
    ) AS rn
  FROM filtered
)
SELECT
  md5(
    concat_ws(
      '||',
      taxi_type,
      CAST(pickup_datetime AS VARCHAR),
      CAST(dropoff_datetime AS VARCHAR),
      CAST(pickup_location_id AS VARCHAR),
      CAST(dropoff_location_id AS VARCHAR),
      CAST(COALESCE(d.payment_type_id, -1) AS VARCHAR),
      CAST(COALESCE(trip_distance, -1) AS VARCHAR),
      CAST(COALESCE(total_amount, -1) AS VARCHAR),
      COALESCE(source_month, ''),
      COALESCE(source_url, '')
    )
  ) AS trip_id,
  d.taxi_type,
  d.pickup_datetime,
  d.dropoff_datetime,
  d.pickup_location_id,
  d.dropoff_location_id,
  d.payment_type_id,
  p.payment_type_name,
  d.passenger_count,
  d.trip_distance,
  d.fare_amount,
  d.tip_amount,
  d.total_amount,
  d.source_month,
  d.source_url,
  d.extracted_at
FROM deduplicated d
LEFT JOIN ingestion.payment_lookup p
  ON d.payment_type_id = p.payment_type_id
WHERE d.rn = 1
