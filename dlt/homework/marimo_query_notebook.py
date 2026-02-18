import marimo

__generated_with = "0.19.11"
app = marimo.App()


@app.cell
def _():
    import duckdb
    import marimo as mo
    import pathlib

    return duckdb, mo, pathlib


@app.cell
def _(mo):
    mo.md("""
    # NYC Taxi DuckDB Query Notebook

    Run SQL directly with marimo's `mo.sql(...)` helper.
    """)
    return


@app.cell
def _(mo, pathlib):
    workspace_root = pathlib.Path(__file__).resolve().parents[2]
    default_db_path = workspace_root / "taxi_pipeline.duckdb"

    db_path = mo.ui.text(
        value=str(default_db_path),
        label="DuckDB file path",
        full_width=True,
    )
    mo.vstack([db_path])
    return (db_path,)


@app.cell
def _(db_path, duckdb, mo):
    connection = duckdb.connect(db_path.value, read_only=True)

    tables = mo.sql(
        """
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
        ORDER BY table_schema, table_name
        """,
        engine=connection,
    )

    mo.vstack([mo.md("### Available tables"), tables])
    return (connection,)


@app.cell
def _(mo):
    query = mo.ui.text_area(
        value="SELECT *\nFROM nyc_taxi_trips\nLIMIT 20;",
        label="SQL query",
        full_width=True,
    )
    mo.vstack([query])
    return (query,)


@app.cell
def _(connection, mo, query):
    try:
        result = mo.sql(query.value, engine=connection)
        mo.vstack([mo.md("### Query result"), result])
    except Exception as error:
        mo.md(f"### Query error\n```\n{error}\n```")
    return


@app.cell
def _(connection, mo):
    _df = mo.sql(
        f"""
        WITH
        	credit AS (
        		SELECT COUNT(*) AS credit_payments
        		FROM taxi_pipeline_dataset_20260217101904.nyc_taxi_trips
        		WHERE payment_type = 'Credit'
        	),
        	total AS (
        		SELECT COUNT(*) AS total_payments
        		FROM taxi_pipeline_dataset_20260217101904.nyc_taxi_trips
        		)

        SELECT (credit_payments / total_payments) * 100
        FROM credit, total;
        """,
        engine=connection
    )
    return


if __name__ == "__main__":
    app.run()
