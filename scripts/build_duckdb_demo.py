from __future__ import annotations

import argparse
from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "local_reconciliation_demo.duckdb"


def csv_path(relative_path: str) -> str:
    return (ROOT / relative_path).as_posix()


def execute_sql_files(connection: duckdb.DuckDBPyConnection) -> None:
    for sql_file in [
        "sql/01_raw_to_parsed.sql",
        "sql/02_key_generation.sql",
        "sql/03_reconciliation_logic.sql",
        "sql/04_reporting_views.sql",
        "sql/05_bi_views.sql",
    ]:
        connection.execute((ROOT / sql_file).read_text(encoding="utf-8"))


def build_database(output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()
    wal_path = output_path.with_suffix(output_path.suffix + ".wal")
    if wal_path.exists():
        wal_path.unlink()

    connection = duckdb.connect(database=output_path.as_posix())
    try:
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

        connection.execute(
            """
            create or replace table demo_reconciliation_by_payment_batch as
            select * from reconciliation_by_payment_batch;

            create or replace table demo_reconciliation_by_receipt as
            select * from reconciliation_by_receipt;

            create or replace table demo_receipt_exception_classification as
            select * from receipt_exception_classification;

            create or replace table demo_bi_reconciliation_daily_kpis as
            select * from bi_reconciliation_daily_kpis;

            create or replace table demo_bi_aging_exposure as
            select * from bi_aging_exposure;

            create or replace table demo_bi_exception_backlog as
            select * from bi_exception_backlog;

            create or replace table demo_bi_receipt_exception_summary as
            select * from bi_receipt_exception_summary;

            create or replace table demo_bi_allocation_readiness as
            select * from bi_allocation_readiness;

            create or replace table demo_dataset_summary as
            select 'raw_payment_batches' as object_name, count(*) as row_count from raw_payment_batches
            union all
            select 'raw_receipts', count(*) from raw_receipts
            union all
            select 'raw_gateway_reference_mapping', count(*) from raw_gateway_reference_mapping
            union all
            select 'demo_reconciliation_by_payment_batch', count(*) from demo_reconciliation_by_payment_batch
            union all
            select 'demo_reconciliation_by_receipt', count(*) from demo_reconciliation_by_receipt
            union all
            select 'demo_receipt_exception_classification', count(*) from demo_receipt_exception_classification
            union all
            select 'demo_bi_reconciliation_daily_kpis', count(*) from demo_bi_reconciliation_daily_kpis
            union all
            select 'demo_bi_aging_exposure', count(*) from demo_bi_aging_exposure
            union all
            select 'demo_bi_exception_backlog', count(*) from demo_bi_exception_backlog
            union all
            select 'demo_bi_receipt_exception_summary', count(*) from demo_bi_receipt_exception_summary
            union all
            select 'demo_bi_allocation_readiness', count(*) from demo_bi_allocation_readiness;
            """
        )

        summary = connection.sql(
            """
            select object_name, row_count
            from demo_dataset_summary
            order by object_name;
            """
        ).fetchall()
    finally:
        connection.close()

    print(f"Built DuckDB demo database: {output_path}")
    for object_name, row_count in summary:
        print(f"- {object_name}: {row_count:,} rows")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a local DuckDB database from the sanitized CSV samples and SQL views."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output .duckdb path. Defaults to {DEFAULT_OUTPUT.name}.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = args.output.expanduser().resolve()
    build_database(output_path)


if __name__ == "__main__":
    main()
