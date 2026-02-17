import gzip
import io
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import PurePosixPath
from threading import Lock
from typing import Callable

import enlighten
import pyarrow as pa
import pyarrow.csv as pv
import pyarrow.parquet as pq
import requests
import typer
from google.api_core.exceptions import Forbidden, NotFound
from google.cloud import storage

URL_TEMPLATE = "https://github.com/DataTalksClub/nyc-tlc-data/releases/download/{color}/{color}_tripdata_{year}-{month}.csv.gz"
YEARS = [2019, 2020]
MONTHS = range(1, 13)
COLORS = ["green", "yellow"]

REQUEST_TIMEOUT = (10, 60)
UPLOAD_TIMEOUT = 120
CHUNK_SIZE = 8 * 1024 * 1024


def make_status_logger(status_bar) -> Callable[[str], None]:
    lock = Lock()

    def log(message: str) -> None:
        with lock:
            status_bar.update(message=message)

    return log


def convert_remote_csv_gz_to_parquet_bytes(url: str, color: str) -> bytes:
    with requests.get(url, timeout=REQUEST_TIMEOUT, stream=True) as response:
        response.raise_for_status()

        with gzip.GzipFile(fileobj=response.raw) as gzip_stream:
            if color == "green":
                convert_options = pv.ConvertOptions(
                    column_types={"ehail_fee": pa.float64()}
                )
                table = pv.read_csv(
                    pa.input_stream(gzip_stream), convert_options=convert_options
                )
            else:
                table = pv.read_csv(pa.input_stream(gzip_stream))
            output = pa.BufferOutputStream()
            pq.write_table(table, output, compression="snappy")
            return output.getvalue().to_pybytes()


def create_bucket(bucket_name: str, client: storage.Client) -> storage.Bucket:
    try:
        bucket = client.get_bucket(bucket_name)
        print(f"Bucket '{bucket_name}' exists. Proceeding...")
        return bucket
    except NotFound:
        bucket = client.create_bucket(bucket_name)
        print(f"Created bucket '{bucket_name}'")
        return bucket
    except Forbidden as error:
        typer.echo(
            f"Bucket '{bucket_name}' exists but is not accessible. "
            f"Please use a different bucket name. Details: {error}"
        )
        raise typer.Exit(code=1)


def upload_parquet_bytes(
    bucket: storage.Bucket,
    blob_name: str,
    parquet_payload: bytes,
    log: Callable[[str], None],
    max_retries: int = 3,
) -> bool:
    blob = bucket.blob(blob_name)
    blob.chunk_size = CHUNK_SIZE

    for attempt in range(1, max_retries + 1):
        try:
            log(
                f"Uploading gs://{bucket.name}/{blob_name} (attempt {attempt}/{max_retries})"
            )
            blob.upload_from_file(
                io.BytesIO(parquet_payload),
                size=len(parquet_payload),
                content_type="application/octet-stream",
                timeout=UPLOAD_TIMEOUT,
            )
            if blob.exists(bucket.client):
                log(f"Uploaded gs://{bucket.name}/{blob_name}")
                return True
            log(f"Upload verification failed for gs://{bucket.name}/{blob_name}")
        except Exception as error:
            log(f"Failed upload for gs://{bucket.name}/{blob_name}: {error}")
            time.sleep(5)

    log(f"Giving up on gs://{bucket.name}/{blob_name} after {max_retries} attempts")
    return False


def process_asset(
    color: str,
    year: int,
    month: int,
    bucket: storage.Bucket,
    log: Callable[[str], None],
    max_retries: int,
) -> bool:
    url = URL_TEMPLATE.format(color=color, year=year, month=f"{month:02d}")
    log(f"[+] Processing {color} taxi data for {year}-{month:02d}")

    try:
        parquet_payload = convert_remote_csv_gz_to_parquet_bytes(url, color)
    except requests.RequestException as error:
        log(f"Failed to fetch {url}: {error}")
        return False
    except Exception as error:
        log(f"Failed to convert {url} to parquet: {error}")
        return False

    blob_name = str(
        PurePosixPath(str(year))
        / color
        / f"{color}_tripdata_{year}-{month:02d}.parquet"
    )
    return upload_parquet_bytes(
        bucket, blob_name, parquet_payload, log, max_retries=max_retries
    )


def main(
    project_id: str = typer.Argument(..., help="GCP project ID"),
    bucket_name: str = typer.Argument(..., help="Target GCS bucket name"),
    color: str | None = typer.Option(
        None,
        "--color",
        "-c",
        help="Taxi color to process: yellow or green. Defaults to both.",
        case_sensitive=False,
    ),
    max_retries: int = typer.Option(3, min=1, help="Upload retry attempts"),
    max_workers: int = typer.Option(
        1,
        min=1,
        help="Thread count for parallel uploads (lower uses less memory)",
    ),
):
    client = storage.Client(project=project_id)
    bucket = create_bucket(bucket_name, client)

    selected_colors = COLORS
    if color is not None:
        selected_color = color.lower()
        if selected_color not in COLORS:
            raise typer.BadParameter(
                "Invalid --color value. Use 'yellow' or 'green'.",
                param_hint="--color",
            )
        selected_colors = [selected_color]

    jobs = [
        (job_color, year, month)
        for job_color in selected_colors
        for year in YEARS
        for month in MONTHS
    ]
    total_count = len(jobs)

    success_count = 0
    failed_count = 0

    manager = enlighten.get_manager()
    status_bar = manager.status_bar(
        status_format="{message}",
        message="Initializing upload jobs...",
    )
    log = make_status_logger(status_bar)

    processed_bar = manager.counter(
        total=total_count,
        desc="Processed",
        unit="files",
        bar_format="{desc}{desc_pad}{percentage:3.0f}%|{bar}| {count:d}/{total:d}",
    )
    success_bar = manager.counter(total=total_count, desc="Succeeded", unit="files")
    failed_bar = manager.counter(total=total_count, desc="Failed", unit="files")

    try:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for color, year, month in jobs:
                future = executor.submit(
                    process_asset,
                    color,
                    year,
                    month,
                    bucket,
                    log,
                    max_retries,
                )
                futures[future] = (color, year, month)

            for future in as_completed(futures):
                color, year, month = futures[future]
                try:
                    uploaded = future.result()
                except Exception as error:
                    log(
                        f"Unexpected failure for {color} taxi data {year}-{month:02d}: {error}"
                    )
                    uploaded = False

                processed_bar.update(1)
                log(f"Finished {color} taxi data for {year}-{month:02d}")

                if uploaded:
                    success_count += 1
                    success_bar.update()
                else:
                    failed_count += 1
                    failed_bar.update()
    finally:
        processed_bar.close()
        success_bar.close()
        failed_bar.close()
        status_bar.update(message="Done")
        manager.stop()

    print(f"Completed uploads: {success_count}/{total_count}")

    if failed_count > 0:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    typer.run(main)
