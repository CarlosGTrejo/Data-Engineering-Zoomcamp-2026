from typing import Annotated

import dlt
import pandas as pd
import typer
from dlt.common.schema import TTableSchema
from dlt.common.typing import TDataItems
from dlt.sources.rest_api import rest_api_source

URL = "https://jsonplaceholder.typicode.com/"


@dlt.destination()
def to_parquet(items: TDataItems, table: TTableSchema) -> None:
    pd.DataFrame(items).to_parquet(f"{table['name']}.parquet")


def main(count: Annotated[int, typer.Option(help="Number of users to process")] = 10):
    """
    A simple pipeline that processes a specified number of users.
    """
    source = rest_api_source(
        {
            "client": {"base_url": URL},
            "resources": [
                {
                    "name": "users",
                    "endpoint": {
                        "path": "users",
                    },
                }
            ],
        }
    )

    pipeline = dlt.pipeline("json_to_parquet", destination=to_parquet)
    pipeline.run(source, table_name="users")


if __name__ == "__main__":
    typer.run(main)
