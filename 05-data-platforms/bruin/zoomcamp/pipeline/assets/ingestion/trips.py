"""@bruin

# TODO: Set the asset name (recommended pattern: schema.asset_name).
# - Convention in this module: use an `ingestion.` schema for raw ingestion tables.
name: ingestion.trips

# Docs: https://getbruin.com/docs/bruin/assets/python
type: python

image: python:3.14

# TODO: Set the connection.
connection: duckdb-default

# TODO: Choose materialization (optional, but recommended).
# Bruin feature: Python materialization lets you return a DataFrame (or list[dict]) and Bruin loads it into your destination.
# This is usually the easiest way to build ingestion assets in Bruin.
# Alternative (advanced): you can skip Bruin Python materialization and write a "plain" Python asset that manually writes
# into DuckDB (or another destination) using your own client library and SQL. In that case:
# - you typically omit the `materialization:` block
# - you do NOT need a `materialize()` function; you just run Python code
# Docs: https://getbruin.com/docs/bruin/assets/python#materialization
materialization:
  type: table
  strategy: append

# TODO: Define output columns (names + types) for metadata, lineage, and quality checks.
# Tip: mark stable identifiers as `primary_key: true` if you plan to use `merge` later.
# Docs: https://getbruin.com/docs/bruin/assets/columns
# columns:
#   - name: TODO_col1
#     type: TODO_type
#     description: TODO

@bruin"""

import io
import json
import os
from datetime import date, datetime, timedelta, timezone

import pandas as pd
import requests

BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"


def _month_starts(start_date: date, end_date: date) -> list[date]:
    if end_date <= start_date:
        return []

    current = date(start_date.year, start_date.month, 1)
    end_inclusive = end_date - timedelta(days=1)
    last = date(end_inclusive.year, end_inclusive.month, 1)

    months: list[date] = []
    while current <= last:
        months.append(current)
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)

    return months


def _build_source_urls(
    start_date: date, end_date: date, taxi_types: list[str]
) -> list[tuple[str, str, str]]:
    urls: list[tuple[str, str, str]] = []
    for month_start in _month_starts(start_date, end_date):
        year_month = f"{month_start.year}-{month_start.month:02d}"
        for taxi_type in taxi_types:
            file_name = f"{taxi_type}_tripdata_{year_month}.parquet"
            source_url = f"{BASE_URL}/{file_name}"
            urls.append((taxi_type, year_month, source_url))
    return urls


def _get_taxi_types() -> list[str]:
    vars_payload = os.environ.get("BRUIN_VARS", "{}")
    parsed_vars = json.loads(vars_payload)
    taxi_types = parsed_vars.get("taxi_types", ["green"])

    if not isinstance(taxi_types, list):
        raise ValueError("`taxi_types` must be an array in BRUIN_VARS")

    normalized = [
        str(taxi_type).strip().lower()
        for taxi_type in taxi_types
        if str(taxi_type).strip()
    ]
    if not normalized:
        raise ValueError("`taxi_types` cannot be empty")

    return sorted(set(normalized))


def _download_parquet(url: str) -> pd.DataFrame | None:
    response = requests.get(url, timeout=60)
    if response.status_code == 404:
        return None

    response.raise_for_status()
    return pd.read_parquet(io.BytesIO(response.content))


def materialize():
    start_date = date.fromisoformat(os.environ["BRUIN_START_DATE"])
    end_date = date.fromisoformat(os.environ["BRUIN_END_DATE"])
    taxi_types = _get_taxi_types()
    source_urls = _build_source_urls(start_date, end_date, taxi_types)

    extracted_at = datetime.now(timezone.utc)
    frames: list[pd.DataFrame] = []

    for taxi_type, year_month, source_url in source_urls:
        frame = _download_parquet(source_url)
        if frame is None:
            continue

        frame["taxi_type"] = taxi_type
        frame["source_month"] = year_month
        frame["source_url"] = source_url
        frame["extracted_at"] = extracted_at
        frames.append(frame)

    if not frames:
        raise RuntimeError(
            "No trip files were found for the selected window and taxi types. "
            "Check BRUIN_START_DATE/BRUIN_END_DATE and BRUIN_VARS.taxi_types."
        )

    return pd.concat(frames, ignore_index=True, sort=False)
