from __future__ import annotations

from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parents[1]


def csv_path(relative_path: str) -> str:
    return (ROOT / relative_path).as_posix()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    connection = duckdb.connect(database=":memory:")

    connection.execute(
        "set preserve_insertion_order=false;"
    )
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

    payment_batch_columns = {
        row[0]
        for row in connection.sql(
            """
            select column_name
            from information_schema.columns
            where table_name = 'reconciliation_by_payment_batch'
            """
        ).fetchall()
    }
    require(
        {
            "payment_batch_id",
            "payment_batch_total",
            "linked_receipt_count",
            "linked_receipts",
            "open_line_total",
            "reconciliation_outcome",
        }.issubset(payment_batch_columns),
        f"Unexpected reconciliation_by_payment_batch schema: {payment_batch_columns}",
    )
    require("amount_variance_line_count" not in payment_batch_columns, "Old amount-variance fields should be gone from payment-batch reporting.")
    require("cancellation_fee_line_count" not in payment_batch_columns, "Old cancellation-fee fields should be gone from payment-batch reporting.")
    require("review_reason" not in payment_batch_columns, "Payment-batch reporting should no longer expose review_reason.")

    receipt_columns = {
        row[0]
        for row in connection.sql(
            """
            select column_name
            from information_schema.columns
            where table_name = 'reconciliation_by_receipt'
            """
        ).fetchall()
    }
    require(
        {
            "receipt_ref",
            "receipt_total",
            "chargeback_line_count",
            "rejected_line_count",
            "linked_payment_batches",
            "reconciliation_outcome",
        }.issubset(receipt_columns),
        f"Unexpected reconciliation_by_receipt schema: {receipt_columns}",
    )
    require("cancellation_fee_receipt_line_count" not in receipt_columns, "Old cancellation-fee receipt fields should be gone from receipt reporting.")
    require("review_reason" not in receipt_columns, "Receipt reporting should no longer expose review_reason.")

    counts = {
        "payment_batch_summary": connection.sql("select count(*) from reconciliation_by_payment_batch").fetchone()[0],
        "payment_batch_target_summary": connection.sql("select count(*) from payment_batch_receipt_summary").fetchone()[0],
        "receipt_summary": connection.sql("select count(*) from reconciliation_by_receipt").fetchone()[0],
        "receipt_target_summary": connection.sql("select count(*) from receipt_payment_batch_summary").fetchone()[0],
        "receipt_exceptions": connection.sql("select count(*) from receipt_exception_classification").fetchone()[0],
        "daily_kpis": connection.sql("select count(*) from bi_reconciliation_daily_kpis").fetchone()[0],
        "aging_exposure": connection.sql("select count(*) from bi_aging_exposure").fetchone()[0],
        "exception_backlog": connection.sql("select count(*) from bi_exception_backlog").fetchone()[0],
        "channel_health": connection.sql("select count(*) from bi_channel_health").fetchone()[0],
    }
    for name, value in counts.items():
        require(value > 0, f"{name} should not be empty.")

    outcomes = {
        row[0]
        for row in connection.sql(
            "select distinct reconciliation_outcome from reconciliation_by_receipt"
        ).fetchall()
    }
    require("CHARGEBACK" in outcomes, "Receipt reporting should expose chargeback outcomes.")
    require("REJECTED_RECEIPT" in outcomes, "Receipt reporting should expose rejected receipt outcomes.")
    composite_targets = connection.sql(
        """
        select count(*)
        from receipt_payment_batch_summary
        where payment_batch_id like '%,%'
        """
    ).fetchone()[0]
    require(composite_targets == 0, "Receipt target summary should never collapse multiple payment batches into a comma-separated target.")

    print("DuckDB validation passed: runtime SQL builds the compact live reporting layer without snapshot CSVs.")


if __name__ == "__main__":
    main()
