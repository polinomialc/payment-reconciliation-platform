from __future__ import annotations

import csv
from pathlib import Path

import duckdb

from build_duckdb_demo import ROOT, csv_path, execute_sql_files


GENERATED_DIR = ROOT / "metabase" / "generated"


def public_status(value: object) -> object:
    mapping = {
        "MATCH": "Matched",
        "CHECK": "Review",
        "MISSING_REFERENCE": "Review",
        "REJECTED": "Rejected transaction",
        "REJECTED_CARD_TRANSACTION": "Rejected transaction",
        "CHARGEBACK": "Chargeback",
        "UNLINKED": "Unlinked receipt",
    }
    return mapping.get(value, value)


def public_target(value: object) -> object:
    mapping = {
        "CHECK": "Review queue",
        "MISSING_REFERENCE": "Review queue",
        "REJECTED": "Rejected transaction",
        "CHARGEBACK": "Chargeback",
        "UNLINKED": "Unlinked receipt",
    }
    return mapping.get(value, value)


def public_composite_status(value: object) -> object:
    if value is None:
        return value
    parts = [part.strip() for part in str(value).split(",")]
    return ", ".join(str(public_status(part)) for part in parts)


def write_csv(output_path: Path, columns: list[str], rows: list[tuple[object, ...]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        writer.writerows(rows)


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
        payment_batch_rows = []
        for row in connection.sql(
            """
            select
                payment_batch_id,
                transaction_date,
                market_code,
                channel_type,
                payment_batch_total,
                reconciliation_target as linked_to,
                line_count,
                linked_amount,
                line_statuses
            from payment_batch_receipt_summary
            order by transaction_date, payment_batch_id, reconciliation_target
            """
        ).fetchall():
            (
                payment_batch_id,
                transaction_date,
                market_code,
                channel_type,
                payment_batch_total,
                linked_to,
                line_count,
                linked_amount,
                line_statuses,
            ) = row
            payment_batch_rows.append(
                (
                    payment_batch_id,
                    transaction_date,
                    market_code,
                    channel_type,
                    payment_batch_total,
                    public_target(linked_to),
                    line_count,
                    linked_amount,
                    public_composite_status(line_statuses),
                )
            )
        write_csv(
            GENERATED_DIR / "reconciliation_by_payment_batch.csv",
            [
                "payment_batch_id",
                "transaction_date",
                "market_code",
                "channel_type",
                "payment_batch_total",
                "linked_to",
                "line_count",
                "linked_amount",
                "line_statuses",
            ],
            payment_batch_rows,
        )
        receipt_totals = {
            (receipt_ref, transaction_date, market_code, channel_type): receipt_total
            for receipt_ref, transaction_date, market_code, channel_type, receipt_total in connection.sql(
                """
                select
                    receipt_ref,
                    transaction_date,
                    market_code,
                    channel_type,
                    receipt_total
                from reconciliation_by_receipt
                """
            ).fetchall()
        }
        receipt_rows = []
        for row in connection.sql(
            """
            select
                receipt_ref,
                transaction_date,
                market_code,
                channel_type,
                payment_batch_id as linked_to,
                line_count,
                linked_amount,
                line_statuses
            from receipt_payment_batch_summary
            order by transaction_date, receipt_ref, payment_batch_id
            """
        ).fetchall():
            receipt_ref, transaction_date, market_code, channel_type, linked_to, line_count, linked_amount, line_statuses = row
            receipt_rows.append(
                (
                    receipt_ref,
                    transaction_date,
                    market_code,
                    channel_type,
                    receipt_totals[(receipt_ref, transaction_date, market_code, channel_type)],
                    public_target(linked_to),
                    line_count,
                    linked_amount,
                    public_composite_status(line_statuses),
                )
            )
        write_csv(
            GENERATED_DIR / "reconciliation_by_receipt.csv",
            [
                "receipt_ref",
                "transaction_date",
                "market_code",
                "channel_type",
                "receipt_total",
                "linked_to",
                "line_count",
                "linked_amount",
                "line_statuses",
            ],
            receipt_rows,
        )
        receipt_exception_rows = []
        for row in connection.sql(
            """
            select
                receipt_ref,
                transaction_date,
                market_code,
                channel_type,
                transaction_status,
                receipt_exception_type,
                gross_amount,
                net_amount,
                your_reference
            from receipt_exception_classification
            order by transaction_date, receipt_ref, receipt_exception_type
            """
        ).fetchall():
            (
                receipt_ref,
                transaction_date,
                market_code,
                channel_type,
                transaction_status,
                receipt_exception_type,
                gross_amount,
                net_amount,
                your_reference,
            ) = row
            receipt_exception_rows.append(
                (
                    receipt_ref,
                    transaction_date,
                    market_code,
                    channel_type,
                    transaction_status,
                    public_status(receipt_exception_type),
                    gross_amount,
                    net_amount,
                    your_reference,
                )
            )
        write_csv(
            GENERATED_DIR / "receipt_exception_classification.csv",
            [
                "receipt_ref",
                "transaction_date",
                "market_code",
                "channel_type",
                "transaction_status",
                "receipt_exception_type",
                "gross_amount",
                "net_amount",
                "your_reference",
            ],
            receipt_exception_rows,
        )
    finally:
        connection.close()

    print(f"Exported Metabase seed files to: {GENERATED_DIR}")


if __name__ == "__main__":
    main()
