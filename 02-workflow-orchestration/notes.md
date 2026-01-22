# Workflow Orchestration (with Kestra)

## 2.1 Introduction to Workflow Orchestration

### 2.1.1 What is Workflow Orchestration?
Workflow orchestration is the automated process of managing and coordinating complex data workflows and tasks. It involves scheduling, executing, and monitoring a series of interdependent tasks to ensure that data is processed efficiently and reliably.
In data engineering, workflow orchestration is crucial for automating ETL (Extract, Transform, Load) processes, data pipelines, and other data-related tasks. It helps ensure that data flows smoothly from source to destination while handling dependencies, failures, and retries.

### 2.1.2 What is Kestra?
Kestra is an open-source workflow orchestration platform designed to manage and automate complex data workflows.
**Features**
- Build with Flow code (YAML), No-Code, or AI copilot
- 1000+ plugins for various integrations
- Language agnostic
- Full Observability and Monitoring
- Schedule and event-based triggers

## 2.2 Getting Started with Kestra
### 2.2.1 Installing Kestra

We'll use a [Docker Compose file](docker-compose.yml) to set up our Kestra project, which will include:
- 3 volumes (NY Taxi dataset, kestra postgres data, and kestra data)
- 4 services (postgres, pgAdmin, Kestra Postgres, Kestra)