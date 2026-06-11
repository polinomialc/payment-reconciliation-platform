#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?Set PROJECT_ID to your Google Cloud project id.}"
DATASET="${BIGQUERY_DATASET:-payment_reconciliation_demo}"
LOCATION="${BIGQUERY_LOCATION:-EU}"
PYTHON_BIN="${PYTHON:-python3}"

"${PYTHON_BIN}" scripts/export_bigquery_seed.py

bq --location="${LOCATION}" mk --dataset --description "Payment reconciliation portfolio demo" "${PROJECT_ID}:${DATASET}" 2>/dev/null || true

bq load --replace --source_format=CSV --skip_leading_rows=1 --autodetect "${PROJECT_ID}:${DATASET}.raw_payment_batches" sample_data/payment_batches_sample.csv
bq load --replace --source_format=CSV --skip_leading_rows=1 --autodetect "${PROJECT_ID}:${DATASET}.raw_receipts" sample_data/receipts_sample.csv
bq load --replace --source_format=CSV --skip_leading_rows=1 --autodetect "${PROJECT_ID}:${DATASET}.raw_gateway_reference_mapping" sample_data/gateway_reference_mapping_sample.csv

for table in \
  reconciled_payment_batch_lines \
  reconciled_receipt_lines \
  reconciliation_by_payment_batch \
  payment_batch_receipt_summary \
  reconciliation_by_receipt \
  receipt_payment_batch_summary \
  receipt_exception_classification \
  reconciliation_runtime_summary
do
  bq load --replace --source_format=CSV --skip_leading_rows=1 --autodetect \
    "${PROJECT_ID}:${DATASET}.${table}" "bigquery/generated/${table}.csv"
done

echo "Loaded BigQuery demo dataset: ${PROJECT_ID}.${DATASET}"
