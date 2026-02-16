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

