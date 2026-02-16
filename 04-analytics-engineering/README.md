# Analytics Engineering

## Setup

We need our data in bigquery to do the analytics engineering work. We will load the data from 2019 and 2020 for both green and yellow taxi data through external tables. We will use the following steps to load the data:

1. Run the `load_taxi_data.py` script.
2. While that runs in the background, you can create a new dataset in bigquery called `taxi_data` to hold the external tables. You can do this through the bigquery UI by clicking on the actions button of your project and selecting "Create dataset". Then, you can fill in the details as follows:
   - Dataset ID: `module4` (or whatever name you prefer)
   - Data location: `us-south1` (or whatever location you prefer)
3. After the script finishes, run the following SQL queries in the bigquery console to create the external tables:

   ```sql
   CREATE OR REPLACE EXTERNAL TABLE module4.yellow_external
   OPTIONS (
     format = 'PARQUET',
     uris = ['gs://de-zoomcamp-2026-taxi-data/2019/yellow/*', 'gs://de-zoomcamp-2026-taxi-data/2020/yellow/*']
   );

   CREATE OR REPLACE EXTERNAL TABLE module4.green_external
   OPTIONS (
     format = 'PARQUET',
     uris = ['gs://de-zoomcamp-2026-taxi-data/2019/green/*', 'gs://de-zoomcamp-2026-taxi-data/2020/green/*']
   );
   ```

If everything goes well you should see the external tables in bigquery. Now you need to:

1. Create a dbt account
2. Create a project
3. Configure the bigquery connection
   - Use same region as the dataset you created in step 2
   - Provide a service account JSON key with the following permissions:
     - BigQuery Data Editor
     - BigQuery Job User
     - BigQuery User
   - daset name: `dbt_prod`
   - timeout: 300 seconds
   - Optional: set maximum bytes billed to `1000000000` to avoid unexpected costs and prevent runaway queries.
   - Click "Test Connection" (it can take a few seconds to run) and then "Save"
4. Setup a repository to store project code

You can now click on "Studio" and then on "Initialize project", then you should be good to go.

### Environments in dbt

In dbt, **environments** define different contexts where your data transformations run:

- **Development Environment**: Your personal workspace for building and testing models
  - Uses your personal credentials
  - Creates temporary schemas with your name (e.g., `dbt_<your_name>`)
  - Changes only affect your work, not production
  - Used when working in the dbt Cloud IDE

- **Deployment Environment**: The production workspace where final models run on schedule
  - Uses service account credentials
  - Creates production schemas (e.g., `dbt_prod_staging`, `dbt_prod_marts`)
  - Used by scheduled jobs that keep your data warehouse updated

Think of it like having a draft folder (development) and a published folder (deployment) for your analytics code.

You should already have a "Development" environment set up automatically after creating your project and adding your bigquery connection.
You can verify this by going to Orchestration > Environments on the left sidebar.

## Tools used by analytics engineers

- **Data Loading:** Python, Airflow, etc.
- **Data Storing:** Snowflake, BigQuery, Redshift, etc.
- **Data Modeling:** dbt, Dataform, etc.
- **Data Presentation:** Google Data Studio, Looker, Mode, Tableau, Power BI, etc.

In weeks 1-3 we covered data loading and storing. In this week we will cover data modeling and presentation.

## Data Modeling Concepts

Very brief recap of ETL VS ELT:

ETL

- Slightly more stable and compliant data analysis
- Higher storage and compute costs

ELT

- Faster and more flexible data analysis
- Lower cost and lower maintenance

## Kimball's Dimensional Modeling Overview

- Objective:
  - Deliver data understandable to the business users
  - Deliver fast query perfomrance
- Approach:
  - Prioritize user understability and query performance over non redundant data (3NF)
- Other approaches:
  - Bill Inmon
  - Data Vault

## Elements of Dimensional Modeling

Facts tables

- Measurements, metrics or facts
- Corresponds to a business process
- "verbs"

Dimension tables

- Corresponds to a business entity
- Provides context to a business process
- "nouns"

### Architecture of Dimensional Modeling

Stage Area

- Contains raw data from source systems
- Not meant to be exposed to end users

Processing area

- From raw data to data models
- Focuses in efficiency
- Ensuring standards

Presentation area

- Final presentation of data to end users
- Exposure to business stakeholders

## dbt project structure

### analyses/

- A place for SQL files that you don't want to expose to end users
- Can be used for data quality reports
- Not used by a lot of people, but can be useful for storing SQL files that are not models

### dbt_project.yml

- most important file in dbt
- contains configuration for the project
- needed to run dbt commands
- for dbt core, your profile should match the one in `.dbt/profiles.yml`

### macros/

- behave like python functions (reusable code)
- help encapsulate complex logic that you want to reuse across models
- can be tested independently

### README.md

- documentation for the project
- installation/setup guides
- contact info

### seeds/

- place to upload CSV and flat files (to add them to dbt later)
- quick and dirty approach (better to fix at source)
- can be used for small lookup tables or reference data

### snapshots/

- "take a picture" of a table at a specific point in time
- useful for tracking the history of a column that changes over time (e.g. status of an order)

### tests/

- place to put assertions in SQL format
- place for singular tests
- eg. if this SQL command returns more than 0 rows, then the dbt build fails

### models/

#### staging/

- sources (like raw table from database)
- staging files are 1-to-1 copy of your data with minimal cleaning steps
  - Data types
  - Renaming columns

#### intermediate/

- tables that are not ready for consumption but are used to build the final tables in marts
- Anything that is not raw nor you want to expose
- No guidelines, just nice for heavy duty cleaning or complex logic

#### marts/

- If it is in marts, it is ready for consumption
- tables ready for dashboards
- properly modeled, clean tables

## documentation in dbt

Using yaml files you can add documentation for almost anything in dbt:

- models
- macros
- sources
- tests
- etc.

This documentation can be rendered in a nice format using the `dbt docs generate` command, which creates a JSON file that contains all the docs and info about your dbt models and a static website that you can view with `dbt docs serve`. This is a great way to share documentation with your team and stakeholders, but does not replace data catalog tools. You can also link models to sources and tests to ensure that your documentation is always up to date with your data models.

## tests in dbt

### Singular tests

These are simple sql statment tests that go in the tests directory.
If the statment returns more than 0 rows, the test fails and the dbt build fails. These are useful for testing specific conditions in your data, such as checking for null values or ensuring that a column has unique values.

```sql
select
  order_id,
  sum(amount) as total_amount
from {{ ref('orders') }}
group by all
having sum(amount) < 0
```

### Source Freshness tests

Source freshness tests are a type of test in dbt that check the freshness of your data sources. They ensure that the data in your source tables is up to date and meets certain criteria. For example, you can set a freshness test to check if the data in a source table is no more than 24 hours old. If the data is older than that, the test will fail and alert you to investigate the issue. This is important for ensuring that your data models are built on reliable and timely data, which is crucial for making informed business decisions.

They are defined using yaml files in the `sources` directory. You can specify the freshness criteria, such as the maximum age of the data, and dbt will automatically check this during the build process, or you can run the freshness tests separately using the `dbt source freshness` command.

### Generic tests

Within your model yaml files (like `sources.yml` in our case), you can define 4 kinds of generic tests that can be applied to any column in your models:

- **not_null**: checks that a column does not contain any null values
- **unique**: checks that all values in a column are unique
- **accepted_values**: checks that all values in a column are within a specified list of accepted values
- **relationships**: checks that values in a column have corresponding values in another table

## Custom Generic tests

Although dbt provides 4 built-in generic tests, you can create your own using sql files and jinja under `tests/generic/`. 


```sql
{% test warn_if_odd(model, column_name) %}
  {{ config(severity='warn') }}
  
  select *
  from {{ model }}
  where mod({{ column_name }}, 2) = 1
{% endtest %}
```

## Unit tests

Unit tests in dbt are tests that check the logic of your models at a granular level. They are defined as SQL files in the `tests` directory and can be run independently of the dbt build process. Unit tests are useful for testing specific transformations or calculations in your models to ensure they are producing the expected results. For example, you might create a unit test to check that a calculated column is returning the correct values based on known inputs. If the unit test fails, it indicates that there is an issue with the logic in your model that needs to be addressed before it can be used for analysis or reporting.

They can also be used to test for data quality issues that have not shown up yet.

Unit test:

```sql
-- Unit test for valid email addresses

with customers as (
  select * from {{ ref('stg_customers') }}
),

check_valid_emails as (
  select
    regexp_like(
      email,
      r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    ) as is_valid_email
  from customers
)

select * from check_valid_emails
```

Fixture file:

```yml
unit_tests:
  - name: test_is_valid_email
    description: "Check is_valid_email_address logic captures all known edge cases."
    model: my_model
    given:
      - input: ref('stg_customers')
        rows:
          - {email: cool@example.com}
          - {email: cool@unknown.com}
          - {email: badgmail.com}
          - {email: missingdot@gmailcom}
    expect:
      rows:
        - {email: cool@example.com, is_valid_email: true}
        - {email: cool@unknown.com, is_valid_email: true}
        - {email: badgmail.com, is_valid_email: false}
        - {email: missingdot@gmailcom, is_valid_email: false}
```

## Model Contracts

Model contracts can be added in your models yaml file under `config` and are a way to enforce certain conditions on your models. For example, you can specify that a model should always have a certain column, or that a column should always be of a certain data type. If the model does not meet the contract, the dbt build will fail. This is useful for ensuring that your models are consistent and meet certain standards before they are used for analysis or reporting.

```yml
models:
  - name: my_model
    config:
      contracts:
        enforced: true
    columns:
      - name: id
        data_type: int
        contraints:
          - type: not_null
      - name: customer_name
        data_type: string
        ...
```

## dbt packages

To use a package, create a `packages.yml` file in the root of your dbt project and add the package name and version you want to use. Then run `dbt deps` to install the package.

### dbt_utils

contains a collection of useful macros and functions that can be used in your dbt project.

### dbt_project_evaluator

evaluates your dbt project based on good practices and provides feedback on how to improve your project structure, naming conventions, and other aspects of your dbt project.

### codegen

Helps generate yaml files for models.

### dbt_expectations

Provides a set of pre-built tests that you can use in your dbt project to validate your data. It includes tests for common data quality issues, such as null values, duplicates, and outliers, as well as more complex tests for specific data patterns and relationships. By using dbt_expectations, you can easily add robust testing to your dbt project and ensure that your data is accurate and reliable.

## SQL Refresher

### Window functions

A window function performs a calculation across a set of table rows that are related to the current row. Unlike aggregate functions, rows retain their separate identities.

Syntax: `FUNCTION() OVER (PARTITION BY ... ORDER BY ...)`

#### Row Number

`ROW_NUMBER()` returns the sequential number of a row within a partition of a result set, starting at 1 for the first row in each partition. It is commonly used for removing duplicates or selecting the top N records per group.

```sql
SELECT
  total_amount,
  PULocationID,
  ROW_NUMBER() OVER (PARTITION BY PULocationID ORDER BY total_amount DESC) AS ranking
FROM greentaxi_trips
LIMIT 10;
```

| total_amount | PULocationID | ranking |
| ------------ | ------------ | ------- |
| 86.42        | 234          | 1       |
| 73.5         | 234          | 2       |
| 62.7         | 234          | 3       |
| ...          | ...          | ...     |
| 8.51         | 224          | 1       |
| 8.3          | 224          | 2       |


#### Rank and Dense Rank

- `RANK()`: Assigns a rank, skipping numbers if there are ties (e.g., 1, 2, 2, 4).
- `DENSE_RANK()`: Assigns a rank without skipping numbers (e.g., 1, 2, 2, 3).

```sql
SELECT
  Score,
  RANK() OVER (ORDER BY Score DESC) as Rank,
  DENSE_RANK() OVER (ORDER BY Score DESC) as Dense_Rank
FROM scores
```

| Score | RANK() | DENSE_RANK() |
| ----- | ------ | ------------ |
| 95    | 1      | 1            |
| 90    | 2      | 2            |
| 90    | 2      | 2            |
| 85    | 4      | 3            |


#### Lag and Lead

- `LAG()`: Accesses data from a previous row.
- `LEAD()`: Accesses data from a subsequent row.

These are useful for comparing the current row with previous or next values without needing self-joins.

```sql
SELECT
  lpep_pickup_datetime,
  total_amount,
  LAG(total_amount) OVER (ORDER BY lpep_pickup_datetime) as prev_total_amount,
  LEAD(total_amount) OVER (ORDER BY lpep_pickup_datetime) as next_total_amount
FROM greentaxi_trips
ORDER BY lpep_pickup_datetime;
```

| lpep_pickup_datetime    | total_amount | prev_total_amount | next_total_amount |
| ----------------------- | ------------ | ----------------- | ----------------- |
| 2008-12-31 23:33:38 UTC | 7.3          | NULL              | 5.3               |
| 2008-12-31 23:42:31 UTC | 5.3          | 7.3               | 14.55             |
| 2008-12-31 23:47:51 UTC | 14.55        | 5.3               | 19.55             |
| 2008-12-31 23:57:46 UTC | 19.55        | 14.55             | 9.8               |


#### Percentile Cont

Calculates the specified percentile value for the distribution of values.

```sql
SELECT
  PULocationID,
  total_amount,
  PERCENTILE_CONT(total_amount, 0.9) OVER (PARTITION BY PULocationID) AS p90
FROM greentaxi_trips;
```

| PULocationID | total_amount | p90  |
| ------------ | ------------ | ---- |
| 224          | 17.3         | 51.9 |
| 224          | 20.67        | 51.9 |
| ...          | ...          | ...  |
| 224          | 55.46        | 51.9 |


### Common Table Expressions (CTEs)

A CTE is a temporary result set that you can reference within a SELECT, INSERT, UPDATE, or DELETE statement. It makes complex queries more readable and maintainable by breaking them into smaller, logical building blocks.

```sql
WITH cte AS (
   

| lpep_pickup_datetime    | total_amount | rank |
| ----------------------- | ------------ | ---- |
| 2019-10-10 15:22:49 UTC | 2878.3       | 2    |
 SELECT
        lpep_pickup_datetime,
        total_amount,
        RANK() OVER (ORDER BY total_amount DESC) AS rank
    FROM greentaxi_trips
)
SELECT * FROM cte
WHERE rank = 2;
```

### dbt models and CTEs

CTEs are heavily used in dbt to structure transformations. A common pattern is to define a CTE for your source data or intermediate calculations and then select from it.

```sql
-- Calculating trip duration and the 90th percentile
WITH trip_duration_calculated AS (
    SELECT
        *,
        timestamp_diff(dropOff_datetime, pickup_datetime, second) as trip_duration
    FROM `fhv_trips`
)
SEL

| PUlocationID | trip_duration | trip_duration_p90 |
| ------------ | ------------- | ----------------- |
| 190          | 451           | 2170.0            |
| 190          | 1373          | 2170.0            |
| ...          | ...           | ...               |
| 32           | 546           | 1988.0            |
| 32           | 151           | 1988.0            |
ECT
    PUlocationID,
    trip_duration,
    PERCENTILE_CONT(trip_duration, 0.90) OVER (PARTITION BY PUlocationID) AS trip_duration_p90
FROM trip_duration_calculated
```

