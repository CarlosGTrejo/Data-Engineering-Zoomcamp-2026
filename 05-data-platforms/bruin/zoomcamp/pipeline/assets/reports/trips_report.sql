/* @bruin

# Docs:
# - SQL assets: https://getbruin.com/docs/bruin/assets/sql
# - Materialization: https://getbruin.com/docs/bruin/assets/materialization
# - Quality checks: https://getbruin.com/docs/bruin/quality/available_checks

# TODO: Set the asset name (recommended: reports.trips_report).
name: reports.trips_report

# TODO: Set platform type.
# Docs: https://getbruin.com/docs/bruin/assets/sql
# suggested type: duckdb.sql
type: duckdb.sql

# TODO: Declare dependency on the staging asset(s) this report reads from.
depends:
  - staging.trips

# TODO: Choose materialization strategy.
# For reports, `time_interval` is a good choice to rebuild only the relevant time window.
# Important: Use the same `incremental_key` as staging (e.g., pickup_datetime) for consistency.
materialization:
  type: table
  # suggested strategy: time_interval
  strategy: time_interval
  # TODO: set to your report's date column
  incremental_key: pickup_datetime
  # TODO: set to `date` or `timestamp`
  time_granularity: timestamp

# TODO: Define report columns + primary key(s) at your chosen level of aggregation.
columns:
  - name: pickup_datetime
    type: timestamp
    description: Start of the day bucket for report aggregation.
    primary_key: true
    nullable: false
    checks:
      - name: not_null
  - name: taxi_type
    type: string
    description: Taxi type (yellow/green).
    primary_key: true
    nullable: false
    checks:
      - name: not_null
  - name: payment_type_id
    type: integer
    description: Payment type identifier.
    primary_key: true
  - name: payment_type_name
    type: string
    description: Human-readable payment type.
  - name: trip_count
    type: bigint
    description: Number of trips in the aggregation bucket.
    checks:
      - name: non_negative
  - name: total_passengers
    type: bigint
    description: Total passenger count across trips.
    checks:
      - name: non_negative
  - name: total_distance
    type: double
    description: Sum of trip distance in miles.
    checks:
      - name: non_negative
  - name: total_fare_amount
    type: double
    description: Sum of fare amount across trips.
    checks:
      - name: non_negative
  - name: total_tip_amount
    type: double
    description: Sum of tip amount across trips.
    checks:
      - name: non_negative
  - name: total_amount
    type: double
    description: Sum of total charged amount across trips.
    checks:
      - name: non_negative
  - name: avg_trip_distance
    type: double
    description: Average trip distance in miles.
    checks:
      - name: non_negative
  - name: avg_total_amount
    type: double
    description: Average charged amount per trip.
    checks:
      - name: non_negative

custom_checks:
  - name: row_count_positive
    description: Ensure the report table is not empty for processed intervals
    query: SELECT COUNT(*) > 0 FROM reports.trips_report
    value: 1

@bruin */

-- Purpose of reports:
-- - Aggregate staging data for dashboards and analytics
-- Required Bruin concepts:
-- - Filter using `{{ start_datetime }}` / `{{ end_datetime }}` for incremental runs
-- - GROUP BY your dimension + date columns

SELECT
  date_trunc('day', pickup_datetime) AS pickup_datetime,
  taxi_type,
  payment_type_id,
  COALESCE(payment_type_name, 'unknown') AS payment_type_name,
  COUNT(*) AS trip_count,
  CAST(SUM(COALESCE(passenger_count, 0)) AS BIGINT) AS total_passengers,
  SUM(COALESCE(trip_distance, 0)) AS total_distance,
  SUM(COALESCE(fare_amount, 0)) AS total_fare_amount,
  SUM(COALESCE(tip_amount, 0)) AS total_tip_amount,
  SUM(COALESCE(total_amount, 0)) AS total_amount,
  AVG(COALESCE(trip_distance, 0)) AS avg_trip_distance,
  AVG(COALESCE(total_amount, 0)) AS avg_total_amount
FROM staging.trips
WHERE pickup_datetime >= TIMESTAMP '{{ start_datetime }}'
  AND pickup_datetime < TIMESTAMP '{{ end_datetime }}'
GROUP BY 1, 2, 3, 4
