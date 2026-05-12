from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parents[1]


def read_csv(relative_path: str) -> list[dict[str, str]]:
    with (ROOT / relative_path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def csv_path(relative_path: str) -> str:
    return (ROOT / relative_path).as_posix()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def build_runtime() -> duckdb.DuckDBPyConnection:
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
        "sql/05_bi_views.sql",
    ]:
        connection.execute((ROOT / sql_file).read_text(encoding="utf-8"))

    return connection


def main() -> None:
    payment_batches = read_csv("sample_data/payment_batches_sample.csv")
    receipts = read_csv("sample_data/receipts_sample.csv")
    gateway_mapping = read_csv("sample_data/gateway_reference_mapping_sample.csv")

    require(
        len({row["payment_batch_id"] for row in payment_batches}) == 3,
        "The compact public sample should expose exactly 3 payment batches.",
    )
    require(
        len({row["receipt_ref"] for row in receipts}) == 5,
        "The compact public sample should expose exactly 5 receipts.",
    )
    require(len(gateway_mapping) > 0, "Gateway-token mapping sample should not be empty.")
    require(
        any(row["channel_type"] == "E_COMMERCE" for row in receipts),
        "Missing e-commerce receipt coverage.",
    )
    require(
        any(row["channel_type"] == "CARD_PRESENT" for row in receipts),
        "Missing card-present receipt coverage.",
    )
    require(
        all(
            len({row["channel_type"] for row in receipts if row["receipt_ref"] == receipt_ref}) == 1
            for receipt_ref in {row["receipt_ref"] for row in receipts}
        ),
        "A single receipt should never mix channels in the public sample.",
    )

    connection = build_runtime()
    try:
        by_payment_batch = connection.sql(
            """
            select payment_batch_id, linked_receipt_count, reconciliation_outcome
            from reconciliation_by_payment_batch
            order by payment_batch_id
            """
        ).df().to_dict("records")

        by_receipt = connection.sql(
            """
            select receipt_ref, reconciliation_outcome
            from reconciliation_by_receipt
            order by receipt_ref
            """
        ).df().to_dict("records")

        receipt_exceptions = connection.sql(
            """
            select receipt_ref, receipt_exception_type
            from receipt_exception_classification
            order by receipt_ref, receipt_exception_type
            """
        ).df().to_dict("records")
    finally:
        connection.close()

    batch_status_counts = Counter(row["reconciliation_outcome"] for row in by_payment_batch)
    require(batch_status_counts["CHECK"] > 0, "Missing payment-batch CHECK coverage.")
    require(
        any(int(row["linked_receipt_count"]) >= 2 for row in by_payment_batch),
        "Expected at least one payment batch linked to multiple receipts.",
    )

    receipt_status_counts = Counter(row["reconciliation_outcome"] for row in by_receipt)
    for required_status in ["LINKED_TO_PAYMENT_BATCHES", "CHARGEBACK", "REJECTED_RECEIPT"]:
        require(receipt_status_counts[required_status] > 0, f"Missing receipt status coverage for {required_status}.")

    exception_counts = Counter(row["receipt_exception_type"] for row in receipt_exceptions)
    require(exception_counts["CHARGEBACK"] > 0, "Missing chargeback example in receipt exceptions.")
    require(
        exception_counts["REJECTED_CARD_TRANSACTION"] > 0,
        "Missing rejected transaction example in receipt exceptions.",
    )

    print("Validation passed: compact runtime sample stays readable while covering multi-receipt, check, chargeback, and rejected flows.")


if __name__ == "__main__":
    main()
