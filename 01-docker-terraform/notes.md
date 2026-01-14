## Docker
- Docker is a platform that allows developers to automate the deployment of applications inside lightweight, portable containers.
- Containers package an application and its dependencies together, ensuring consistency across different environments.
- Key concepts:
  - **Dockerfile**: A text file that contains instructions to build a Docker image.
  - **Image**: A read-only template that contains the application and its dependencies.
  - **Container**: A runnable instance of an image.

### Basic Docker Commands
- `docker build -t <image_name> <dir>` : Build a Docker image from a Dockerfile.
- `docker run -it <image_name>` : Run a container from an image interactively.
  - use `--rm` to automatically remove the container when it exits.
  - use `-d` to run the container in detached mode (in the background).
  - use `-p <host_port>:<container_port>` to map ports between the host and the container.
  - use `-v <host_path>:<container_path>` to mount a volume from the host to the container.
- `docker network create <network_name>` : Create a custom Docker network to allow containers to communicate with each other.
- `docker exec -it <container_id> <command>` : Execute a command inside a running container.
- `docker stop <container_id>` : Stop a running container.
- `docker rm <container_id>` : Remove a stopped container.
- `docker ps` : List running containers.
- `docker ps -a` : List all containers (running and stopped).
- `docker system prune` : Remove all stopped containers, unused networks, and dangling images.
- `docker system prune --filter "until=24h"` : Remove all stopped containers, unused networks, and dangling images older than 24 hours.
- `docker image prune` : Remove dangling images.
- `docker container prune` : Remove all stopped containers.
- `docker volume prune` : Remove all unused volumes.

### Dockerfile Basics
- A Dockerfile is a script that contains a series of instructions on how to build a Docker image.
- Common instructions:
  - `FROM <base_image>` : Specifies the base image to use.
    - `slim` variants are smaller versions of base images (e.g., `python:3.9-slim`).
    - `alpine` variants are even smaller, based on Alpine Linux (e.g., `python:3.9-alpine`).
    - `dhi.io` variants are hardened images for improved security (e.g., `dhi.io:node:16`).
      - Common tools might be missing, package managers might be locked down or limited, and some build steps that assume you have extra system utilities may fail.
  - `RUN <command>` : Executes a command during the image build process.
  - `COPY <source> <destination>` : Copies files from the host to the image.
  - `WORKDIR <path>` : Sets the working directory for subsequent instructions in the image.
  - `CMD ["executable", "param1", "param2"]` : Specifies the command to run when a container is started from the image.
  - `ENTRYPOINT ["executable", "param1", "param2"]` : Runs a specific script when the container starts, allowing additional parameters to be passed.
  - `EXPOSE <port>` : Informs Docker that the container listens on the specified network port at runtime, but does not publish the port to the host, it only serves as documentation.
  - `ENV <key>=<value>` : Sets environment variables in the container, but should not be used for sensitive information like passwords since they can be extracted from the image.
  - `VOLUME ["/data"]` : Creates a mount point with the specified path and marks it as holding externally mounted volumes from native host or other containers.
    - You must map the volume when running the container using `-v <host_path>:<container_path>`, if not, Docker will create an anonymous volume.

### Best Practices
- Use official base images when possible for better security and reliability.
- Keep images small by using slim or alpine variants and removing unnecessary files.
- Use dockerignore files to exclude files and directories that are not needed in the image.
- Use multi-stage builds to reduce the final image size by separating build and runtime dependencies.
  - For example, use one stage to build the application and another stage to copy only the necessary artifacts to the final image.
  - Stage 1: `FROM <build_image> AS builder` : Define a build stage.
  - Stage 2: `COPY --from=builder <source> <destination>` : Copy files from a previous build stage.
- Use `SlimToolkit` to inspect, optimize, and debug Docker images. This can help reduce image size and improve security.

### Creating a Pipeline with Docker

We will create a simple pipeline that:
- Runs a Python script inside a Docker container.
- Uses uv as the package manager
- Extracts data from a public API (NYC Taxi data from GitHub Repo)
- Exports the data as a parquet file

#### Process
1. Create venv using uv: `uv init --python 3.13 && uv venv && source ./.venv/bin/activate`
2. Add dependencies:
    - `uv add pandas pyarrow typer enlighten dlt[filesystem,parquet,postgres]`
    - `uv add --dev pgcli`
3. Write the [script](pipeline.py)
4. Create the [dockerfile](Dockerfile)
5. Build the image: `docker build -t pipeline -f ./01-docker-terraform/Dockerfile .`
    - The `-f` flag specifies the path to the Dockerfile.
    - The `.` at the end specifies the build context (current directory, which is the parent directory). Without it, Docker won't be able to find the files to copy into the image. Even if we run the command from the same directory as the files.
6. Verify our pipeline works:
    1. Deploy a test Postgres container: `docker run -it --rm -e POSTGRES_USER="root" -e POSTGRES_PASSWORD="root" -e POSTGRES_DB="ny_taxi" -p 5432:5432 postgres:18`
    2. Load the data into the test database: `python pipeline.py`
    3. Verify data is loaded using pgcli:
        - `pgcli postgresql://root@localhost:5432/ny_taxi`
        - OR `pgcli -h localhost -p 5432 -u root -d ny_taxi`
7. Create a network for our docker containers to communicate: `docker network create pipeline-network`
8. Run postgres in a container:
    - `docker run -it --rm -e POSTGRES_USER="root" -e POSTGRES_PASSWORD="root" -e POSTGRES_DB="ny_taxi" -v postgres_db:/var/lib/postgresql -p 5432:5432 --network=pipeline-network --name postgres_db postgres:18`
9. Run pgAdmin in another container:
    - `docker run -it --rm -e PGADMIN_DEFAULT_EMAIL="admin@admin.com" -e PGADMIN_DEFAULT_PASSWORD="root" -p 8080:80 --network=pipeline-network --name pgadmin dpage/pgadmin4`
10. Deploy the pipeline container to load data into Postgres:
    - for `host` use `postgres_db` (the name of the Postgres container)
    - `docker run -it --rm --network=pipeline-network pipeline --host postgres_db`

---

## SQL Refresher
- When selecting from multiple tables and using a WHERE clause, the default join is an INNER JOIN.
  - An inner join returns only the rows where there is a match in both tables based on the join condition (like the middle section of a venn diagram).
  - If you want to explicitly specify an inner join, you can use `INNER JOIN` or `JOIN`. Then you can ommit the join condition from the WHERE clause and put it in the ON clause.
  - Example:
    ```sql
    SELECT
        tpep_pickup_datetime,
        tpep_dropoff_datetime,
        total_amount,
        CONCAT(zpu."Borough", ' | ', zpu."Zone") AS "pickup_loc",
        CONCAT(zdo."Borough", ' | ', zdo."Zone") AS "dropoff_loc"
    FROM
        yellow_taxi_trips t,
        zones zpu,
        zones zdo
    WHERE
        t."PULocationID" = zpu."LocationID"
        AND t."DOLocationID" = zdo."LocationID"
    LIMIT 100;
    ```
    Can be rewritten as (notice the WHERE clause is gone):
    ```sql
    SELECT
        tpep_pickup_datetime,
        tpep_dropoff_datetime,
        total_amount,
        CONCAT(zpu."Borough", ' | ', zpu."Zone") AS "pickup_loc",
        CONCAT(zdo."Borough", ' | ', zdo."Zone") AS "dropoff_loc"
    FROM
        yellow_taxi_trips t
    JOIN
        zones zpu ON t."PULocationID" = zpu."LocationID"
    JOIN
        zones zdo ON t."DOLocationID" = zdo."LocationID"
    LIMIT 100;
- You can add an alias to a table or column using the `AS` keyword, or simply by placing the alias after the table or column name.
  - Example: `zones zpu` gives the `zones` table an alias of `zpu`.
  - Example: `CONCAT(zpu."Borough", ' | ', zpu."Zone") AS "pickup_loc"` gives the concatenated column an alias of `pickup_loc`.
- You can also reference columns using their index position in the SELECT clause.
  - Example: `ORDER BY 3 DESC` orders the results by the third column in the SELECT clause in descending order.
  - Example: `GROUP BY 1, 2` groups the results by the first and second columns in the SELECT clause.
- Use double quotes `"` for identifiers (table names, column names) that are case-sensitive or contain special characters.
- Use single quotes `'` for string literals.
  - Example: `SELECT * FROM table WHERE column = 'string_value';`
