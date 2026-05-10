from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import duckdb


ROOT = Path(__file__).resolve().parents[1]


def read_csv(relative_path: str) -> list[dict[str, str]]:
    with (ROOT / relative_path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def csv_path(relative_path: str) -> str:
    return (ROOT / relative_path).as_posix()


def normalize(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [{key: str(value) for key, value in row.items()} for row in rows]


def main() -> None:
    connection = duckdb.connect(database=":memory:")

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

    for sql_file in [
        "sql/01_raw_to_parsed.sql",
        "sql/02_key_generation.sql",
        "sql/03_reconciliation_logic.sql",
        "sql/04_reporting_views.sql",
    ]:
        connection.execute((ROOT / sql_file).read_text(encoding="utf-8"))

    payment_batch_rows = normalize(
        connection.sql(
            """
            select
                payment_batch_id,
                coalesce(receipt_ref, '') as receipt_ref,
                match_status,
                row_count,
                printf('%.2f', payment_batch_total) as payment_batch_total
            from reconciliation_by_payment_batch
            order by payment_batch_id, receipt_ref, match_status
            """
        ).df().to_dict("records")
    )

    receipt_rows = normalize(
        connection.sql(
            """
            select
                receipt_ref,
                match_status,
                row_count,
                printf('%.2f', receipt_total) as receipt_total
            from reconciliation_by_receipt
            order by receipt_ref, match_status
            """
        ).df().to_dict("records")
    )

    receipt_exception_rows = normalize(
        connection.sql(
            """
            select
                receipt_ref,
                receipt_transaction_type,
                cast(transaction_date as varchar) as transaction_date,
                printf('%.2f', gross_amount) as gross_amount,
                printf('%.2f', net_amount) as net_amount,
                your_reference
            from receipt_exception_classification
            order by receipt_ref, receipt_transaction_type, your_reference
            """
        ).df().to_dict("records")
    )

    expected_payment_batch_rows = read_csv("output_examples/reconciliation_by_payment_batch.csv")
    expected_receipt_rows = read_csv("output_examples/reconciliation_by_receipt.csv")
    expected_receipt_exception_rows = read_csv("output_examples/receipt_exception_classification.csv")

    if payment_batch_rows != expected_payment_batch_rows:
        raise AssertionError(
            f"payment batch SQL output mismatch:\nactual={payment_batch_rows}\nexpected={expected_payment_batch_rows}"
        )

    if receipt_rows != expected_receipt_rows:
        raise AssertionError(f"receipt SQL output mismatch:\nactual={receipt_rows}\nexpected={expected_receipt_rows}")

    if receipt_exception_rows != expected_receipt_exception_rows:
        raise AssertionError(
            "receipt exception SQL output mismatch:\n"
            f"actual={receipt_exception_rows}\nexpected={expected_receipt_exception_rows}"
        )

    print("DuckDB validation passed: SQL reproduces the published reconciliation outputs.")


if __name__ == "__main__":
    main()
