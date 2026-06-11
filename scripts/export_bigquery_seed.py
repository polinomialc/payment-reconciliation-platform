from __future__ import annotations

import csv
from pathlib import Path

import duckdb

from build_duckdb_demo import ROOT, csv_path, execute_sql_files


GENERATED_DIR = ROOT / "bigquery" / "generated"

TABLES = [
    "reconciled_payment_batch_lines",
    "reconciled_receipt_lines",
    "reconciliation_by_payment_batch",
    "payment_batch_receipt_summary",
    "reconciliation_by_receipt",
    "receipt_payment_batch_summary",
    "receipt_exception_classification",
    "reconciliation_runtime_summary",
]


def export_csv(connection: duckdb.DuckDBPyConnection, table_name: str) -> None:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    relation = connection.sql(f"select * from {table_name}")
    output_path = GENERATED_DIR / f"{table_name}.csv"
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(relation.columns)
        writer.writerows(relation.fetchall())


def build_runtime_connection() -> duckdb.DuckDBPyConnection:
    connection = duckdb.connect(database=":memory:")
    connection.execute("set preserve_insertion_order=false;")
    connection.execute("set threads=1;")
    connection.execute(
        f"""
        create table raw_payment_batches as
        select * from read_csv_auto('{csv_path("sample_data/payment_batches_sample.csv")}', header=true);

        create table raw_receipts as
        select * from read_csv_auto('{csv_path("sample_data/receipts_sample.csv")}', header=true);

        create table raw_gateway_reference_mapping as
        select * from read_csv_auto('{csv_path("sample_data/gateway_reference_mapping_sample.csv")}', header=true);
        """
    )
    execute_sql_files(connection)
    return connection


def main() -> None:
    connection = build_runtime_connection()
    try:
        for table_name in TABLES:
            export_csv(connection, table_name)
    finally:
        connection.close()

    print(f"Exported BigQuery seed files to: {GENERATED_DIR}")


if __name__ == "__main__":
    main()
