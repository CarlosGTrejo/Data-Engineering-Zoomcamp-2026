from datetime import datetime
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import urlparse

import dlt
import typer
from dlt.sources.filesystem import filesystem, read_csv
from dlt.sources.rest_api import rest_api_source


def get_resource_name(url: str) -> str:
    path = Path(urlparse(url).path)
    return path.name


def get_bucket_path(url: str) -> str:
    url_parts = urlparse(url)
    path = Path(url_parts.path)
    return f"{url_parts.scheme}://{url_parts.netloc}{path.parent}/"


def build_pipeline(destination: Literal["postgres", "parquet"]) -> dlt.Pipeline:
    if destination == "postgres":
        pipeline = dlt.pipeline(
            pipeline_name="csv_to_postgres",
            dataset_name="ny_taxi",
            destination=dlt.destinations.postgres(
                "postgresql://root:root@localhost:5432/ny_taxi"
            ),
        )
    else:
        bucket_root = Path(__file__).parent / "parquet_data"
        bucket_root.mkdir(parents=True, exist_ok=True)

        pipeline = dlt.pipeline(
            pipeline_name="csv_to_parquet",
            dataset_name="ny_taxi",
            destination=dlt.destinations.filesystem(bucket_url=str(bucket_root)),
        )
    return pipeline


def main(
    destination: Annotated[
        Literal["postgres", "parquet"],
        typer.Option(help="Save to postgres or as parquet files"),
    ] = "postgres",
    color: Annotated[
        Literal["yellow", "green"], typer.Option(help="Color of the taxi")
    ] = "yellow",
    period: Annotated[
        datetime,
        typer.Option(formats=["%Y-%m"], help="Year and month for data to load"),
    ] = datetime.strptime("2020-01", "%Y-%m"),
):
    period_str: str = period.strftime("%Y-%m")
    release = "71974786" if color == "yellow" else "71979983"
    BASE_URL = "https://api.github.com/"
    PATH = f"repos/DataTalksClub/nyc-tlc-data/releases/{release}/assets"

    # ============= First Stage: Load from GitHub REST API ============= #
    # Extract and Transform
    github_assets = rest_api_source(
        {
            "client": {"base_url": BASE_URL},
            "resources": [
                {
                    "name": "assets",
                    "endpoint": {
                        "path": PATH,
                        "data_selector": "[*].browser_download_url",
                    },
                    "processing_steps": [
                        {"filter": lambda url: period_str in url},
                    ],
                }
            ],
        }
    )

    urls: list[str] = list(github_assets)
    if not urls:
        raise ValueError(f"No data found for {color} taxi for period {period_str}")

    # ============= Second Stage: Save to Postgres OR Parquet============= #
    pipeline = build_pipeline(destination)

    bucket_path = get_bucket_path(urls[0])
    for url in urls:
        bucket_path = get_bucket_path(url)
        resource_name = get_resource_name(url)
        source = (
            filesystem(bucket_url=bucket_path, file_glob=resource_name) | read_csv()
        )
        info = pipeline.run(
            source,
            table_name=f"{color}_taxi",
            loader_file_format="parquet" if destination == "parquet" else "csv",
            write_disposition="append",
        )

        print(info)


if __name__ == "__main__":
    typer.run(main)
