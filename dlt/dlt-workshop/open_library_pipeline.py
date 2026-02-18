"""Template for building a `dlt` pipeline to ingest data from a REST API."""

from dlt.sources.rest_api import rest_api_resources
from dlt.sources.rest_api.typing import RESTAPIConfig

import dlt


@dlt.source
def open_library_rest_api_source():
    """Define dlt resources from REST API endpoints."""
    config: RESTAPIConfig = {
        "client": {
            "base_url": "https://openlibrary.org",
        },
        "resources": [
            {
                "name": "books",
                "endpoint": {
                    "path": "api/books",
                    "params": {
                        "bibkeys": "ISBN:0451526538,ISBN:0201558025",
                        "format": "json",
                        "jscmd": "data",
                    },
                    "data_selector": "$.*",
                },
            }
        ],
    }

    yield from rest_api_resources(config)


pipeline = dlt.pipeline(
    pipeline_name="open_library_pipeline",
    destination="duckdb",
    # `refresh="drop_sources"` ensures the data and the state is cleaned
    # on each `pipeline.run()`; remove the argument once you have a
    # working pipeline.
    refresh="drop_sources",
)


if __name__ == "__main__":
    load_info = pipeline.run(open_library_rest_api_source())
    print(load_info)  # noqa: T201
