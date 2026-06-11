# Cloud Run and BigQuery Deployment

This repository can run locally with DuckDB or in Google Cloud with:

- **BigQuery** as the hosted demo data layer.
- **Cloud Run** as the hosted Streamlit application.
- **Artifact Registry** as the container image registry.
- **Cloud Build** to build the Docker image from `docker/Dockerfile`.

The Cloud Run app supports two data backends:

- `DATA_BACKEND=duckdb`: default local mode. The app loads `sample_data/` and runs the SQL flow in DuckDB.
- `DATA_BACKEND=bigquery`: cloud mode. The app reads materialized demo tables from BigQuery.

## Prerequisites

Install and authenticate the Google Cloud SDK:

```bash
gcloud auth login
gcloud auth application-default login
```

Set your project:

```bash
export PROJECT_ID="your-gcp-project-id"
gcloud config set project "$PROJECT_ID"
```

## 1. Load BigQuery Demo Tables

From the repository root:

```bash
export PROJECT_ID="your-gcp-project-id"
export BIGQUERY_DATASET="payment_reconciliation_demo"
export BIGQUERY_LOCATION="EU"

bash scripts/load_bigquery_demo.sh
```

This creates or replaces:

- raw source tables from `sample_data/`
- reconciliation output tables exported from the local SQL runtime
- receipt exception and runtime summary tables

## 2. Deploy Streamlit To Cloud Run

```bash
export PROJECT_ID="your-gcp-project-id"
export CLOUD_RUN_REGION="europe-west1"
export BIGQUERY_DATASET="payment_reconciliation_demo"

bash scripts/deploy_cloud_run.sh
```

The deploy script:

1. enables required Google Cloud APIs;
2. creates an Artifact Registry repository if needed;
3. builds the Docker image using Cloud Build;
4. grants the Cloud Run service account BigQuery read/query permissions;
5. deploys the Streamlit app with `DATA_BACKEND=bigquery`.

## 3. Verify

After deploy, Cloud Run prints the service URL.

Open it in the browser and verify:

- the home page loads;
- the data backend pill says `BigQuery`;
- the Source Evidence tab shows raw payment batches, receipts, and gateway mappings;
- the reconciliation tabs show matched lines, review queues, chargebacks, and rejected transactions.

## Notes

This cloud deployment uses materialized demo tables in BigQuery so the public portfolio can run without private systems. In a production version, the same pattern would usually keep raw exports in BigQuery and implement the parsing, matching, exception classification, and BI outputs as governed BigQuery views or scheduled transformations.
