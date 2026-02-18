# Getting started with dlt

1. Create a project directory
2. Setup the dlt MCP, if you're using vscode you can do
   1. Ctrl+Shift+P (open command palette)
   2. MCP: Add Server...
   3. Command (stdio)
   4. Paste the command: `uv run --with dlt[duckdb] --with dlt-mcp[search] python -m dlt_mcp`
   5. Name it "dlt"
3. Install dlt: `uv add "dlt[workspace]`
4. Initialize the project: `dlt init dlthub:taxi_pipeline duckdb` (the first argument is the connector/source, the second is the destination)
   - This created the dlt project files and agent rules for ai assistance, but no YAML file for the api metadata.
5. Prompt the agent to create the pipeline, providing API details in the prompt. If you're using VS Code use `#` to link files, tools, and folders.
   ```text
   Build a REST API source for NYC taxi data.

   API details:
   - Base URL: https://us-central1-dlthub-analytics.cloudfunctions.net/data_engineering_zoomcamp_api
   - Data format: Paginated JSON (1,000 records per page)
   - Pagination: Stop when an empty page is returned

   Place the code in taxi_pipeline.py and name the pipeline taxi_pipeline.
   Use @dlt rest api as a tutorial.
   ```
6. After the agent creates a working pipeline and the data is loaded into duckdb, launch the dlt dashboard with:
   ```
   dlt pipeline taxi_pipeline show
   ```
   - You can also ask the agent questions about the pipeline using the dlt MCP server.
   - Build Marimo notebook for visualizations and queries.