from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_csv(relative_path: str) -> list[dict[str, str]]:
    with (ROOT / relative_path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    payment_batches = read_csv("sample_data/payment_batches_sample.csv")
    receipts = read_csv("sample_data/receipts_sample.csv")
    gateway_mapping = read_csv("sample_data/gateway_reference_mapping_sample.csv")
    by_payment_batch = read_csv("output_examples/reconciliation_by_payment_batch.csv")
    by_receipt = read_csv("output_examples/reconciliation_by_receipt.csv")
    receipt_exceptions = read_csv("output_examples/receipt_exception_classification.csv")

    require(len(payment_batches) == len(by_payment_batch), "Each payment batch should have one published status row.")
    require(len(receipts) > len(by_receipt), "Receipt sample should include matched and non-allocation exception rows.")
    require(len(gateway_mapping) > 0, "Gateway-token mapping sample should not be empty.")
    require(len(receipt_exceptions) > 0, "Receipt exception output should not be empty.")

    status_counts = Counter(row["match_status"] for row in by_payment_batch)
    for required_status in ["MATCH", "CFEE", "OVP", "CHECK", "UNMATCHED"]:
        require(status_counts[required_status] > 0, f"Missing sample coverage for {required_status}.")
    require(
        any(row["status"] == "Rejected" for row in receipts),
        "Missing rejected receipt-line coverage.",
    )

    exception_counts = Counter(row["receipt_transaction_type"] for row in receipt_exceptions)
    require(exception_counts["CHARGEBACK"] > 0, "Missing chargeback exception coverage.")
    require(
        exception_counts["REFUND_WITH_CANCELLATION_FEE"] > 0,
        "Missing refund-with-cancellation-fee exception coverage.",
    )

    print("Validation passed: sample data covers all published reconciliation scenarios.")


if __name__ == "__main__":
    main()
