# Data Platforms: Bruin

## What is Bruin?

Bruin is an end-to-end data platform that combines:
- Data ingestion
- Data transformation
- Data quality checks
- Data lineage
- Orchestration
- Metadata

So instead of using several tools to achieve these goals, Bruin provides a single platform to manage all of these aspects of data engineering.

## Installing Bruin

Use the following command to install Bruin:

```bash
curl -LsSf https://getbruin.com/install/cli | sh
```

Then install the Bruin extension for your IDE (VS Code, PyCharm, etc.) to easily manage your Bruin projects.

Then install the Bruin MCP for ai assisted data engineering:

1. Open the command palette in your IDE and search for "MCP: Add Server..."
2. Choose "Command (stdio)"
3. Enter the following command: `bruin mcp`
4. Name the server "bruin"
5. Choose to add it:
   - Globally: If you are doing local development
   - Remotely/Workspace: If you are doing development in GitHub Codespaces
6. You should now see "bruin" listed when you use the "MCP: List Servers" command in vs code.

## Getting Started with Bruin

Inside your bruin project folder, run the `bruin init` command to initialize a new Bruin project (select default for this tutorial). This will create the necessary files and folders for your Bruin project.

The project structure will look like this:

```text
my-first-pipeline/
├── .bruin.yml              # Environment and connection configuration
├── pipeline.yml            # Pipeline name, schedule, default connections
└── assets/
    ├── players.asset.yml   # Ingestr asset (data ingestion)
    ├── player_stats.sql    # SQL asset with quality checks
    └── my_python_asset.py  # Python asset
```

**NEVER PUSH `.bruin.yml` TO VERSION CONTROL, IT CONTAINS SENSITIVE INFORMATION**

### Key CLI commands

| Command                                         | Purpose                                       |
| ----------------------------------------------- | --------------------------------------------- |
| `bruin validate <path>`                         | Check syntax and dependencies without running |
| `bruin run <path>`                              | Execute pipeline or individual asset          |
| `bruin run --downstream`                        | Run asset and all downstream dependencies     |
| `bruin run --full-refresh`                      | Truncate and rebuild tables from scratch      |
| `bruin lineage <path>`                          | View asset dependencies                       |
| `bruin query --connection <conn> --query "..."` | Execute ad-hoc SQL queries                    |

### Configure pipeline.yml

Make sure to add:
- A pipeline name
- A schedule (e.g. daily, hourly, weekly, monthly)
- A start date for backfills
- Default connections (e.g. duckdb: duckdb-default)
- Variables (e.g. taxi_types as an array of strings)
- custom variables if needed (e.g. other_string_var)

