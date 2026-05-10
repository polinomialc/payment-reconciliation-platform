from __future__ import annotations

import csv
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_DATE = date(2026, 2, 1)
MARKETS = ("MKT_A", "MKT_B", "MKT_C", "MKT_D")

ALLOCATION_READY = "Allocation Ready"
CANCELLATION_FEE_REVIEW = "Cancellation Fee Review"
AMOUNT_VARIANCE_REVIEW = "Amount Variance Review"
EVIDENCE_REVIEW = "Evidence Review Required"
MISSING_RECEIPT_EVIDENCE = "Missing Receipt Evidence"


def write_csv(relative_path: str, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with (ROOT / relative_path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def money(index: int) -> Decimal:
    base = Decimal("40.00") + Decimal(index % 89) * Decimal("2.73")
    cents = Decimal(index % 17) / Decimal("100")
    return (base + cents).quantize(Decimal("0.01"))


def market_for(index: int) -> str:
    return MARKETS[index % len(MARKETS)]


def cfee_fee(market_code: str) -> Decimal:
    return Decimal("45.00") if market_code == "MKT_A" else Decimal("50.00")


def append_receipt(
    receipts: list[dict[str, str]],
    receipt_ref: str,
    transaction_date: date,
    market_code: str,
    contract_type: str,
    your_reference: str,
    gross_amount: Decimal,
    *,
    status: str = "Accepted",
    brand: str = "Generic Card",
    transaction_type: str = "Payment",
    net_amount: Decimal | None = None,
) -> None:
    receipt_net_amount = net_amount if net_amount is not None else gross_amount - Decimal("1.25")
    receipts.append(
        {
            "receipt_ref": receipt_ref,
            "transaction_date": transaction_date.isoformat(),
            "market_code": market_code,
            "brand": brand,
            "contract_type": contract_type,
            "status": status,
            "type_of_transaction": transaction_type,
            "your_reference": your_reference,
            "gross_amount": f"{gross_amount:.2f}",
            "net_amount": f"{receipt_net_amount:.2f}",
        }
    )


def append_batch(
    payment_batches: list[dict[str, str]],
    payment_batch_id: str,
    transaction_date: date,
    market_code: str,
    item_description: str,
    amount: Decimal,
    *,
    customer: str = "STANDARD CARD",
) -> None:
    payment_batches.append(
        {
            "payment_batch_id": payment_batch_id,
            "transaction_date": transaction_date.isoformat(),
            "market_code": market_code,
            "customer": customer,
            "item_description": item_description,
            "amount": f"{amount:.2f}",
        }
    )


def append_payment_output(
    output_by_payment_batch: list[dict[str, str]],
    payment_batch_id: str,
    receipt_ref: str,
    reconciliation_outcome: str,
    amount: Decimal,
) -> None:
    output_by_payment_batch.append(
        {
            "payment_batch_id": payment_batch_id,
            "receipt_ref": receipt_ref,
            "reconciliation_outcome": reconciliation_outcome,
            "row_count": "1",
            "payment_batch_total": f"{amount:.2f}",
        }
    )


def append_receipt_output(
    output_by_receipt: list[dict[str, str]],
    receipt_ref: str,
    reconciliation_outcome: str,
    row_count: int,
    receipt_total: Decimal,
) -> None:
    output_by_receipt.append(
        {
            "receipt_ref": receipt_ref,
            "reconciliation_outcome": reconciliation_outcome,
            "row_count": str(row_count),
            "receipt_total": f"{receipt_total:.2f}",
        }
    )


def standard_refs(index: int) -> tuple[str, str, str]:
    reservation_ref = f"{1199000000 + index:010d}"
    invoice_ref = f"{100400000000 + index:012d}"
    acquirer_ref = f"{158000000 + index}"
    return reservation_ref, invoice_ref, acquirer_ref


def build_rows() -> tuple[
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, str]],
]:
    payment_batches: list[dict[str, str]] = []
    receipts: list[dict[str, str]] = []
    gateway_mappings: list[dict[str, str]] = []
    output_by_payment_batch: list[dict[str, str]] = []
    output_by_receipt: list[dict[str, str]] = []
    receipt_exceptions: list[dict[str, str]] = []

    def add_receipt_line(
        receipt_ref: str,
        transaction_date: date,
        market_code: str,
        contract_type: str,
        reservation_ref: str,
        line_index: int,
        amount: Decimal,
        transaction_type: str,
        *,
        status: str = "Accepted",
        reconciliation_outcome: str | None = None,
        batch_amount: Decimal | None = None,
        payment_group_id: str | None = None,
        extra_fee: Decimal | None = None,
    ) -> None:
        token = f"{receipt_ref}-{line_index:04d}"
        receipt_reference = token
        if transaction_type == "Refund With Cancellation Fee":
            receipt_reference = f"{token} REFUND CANCELLATION_FEE"
        elif transaction_type == "Chargeback Adjustment":
            receipt_reference = f"{token} CHARGEBACK"

        append_receipt(
            receipts,
            receipt_ref,
            transaction_date,
            market_code,
            contract_type,
            receipt_reference,
            amount,
            status=status,
            transaction_type=transaction_type,
            net_amount=amount if transaction_type == "Chargeback Adjustment" else None,
        )

        gateway_mappings.append(
            {
                    "gateway_token": token,
                    "merchant_reference": reservation_ref,
                    "transaction_date": transaction_date.isoformat(),
                    "amount": f"{amount:.2f}",
                    "market_code": market_code,
                }
            )

        if reconciliation_outcome and payment_group_id:
            payment_group_amount = batch_amount if batch_amount is not None else amount
            batch_id = f"{payment_group_id}_line_{line_index:04d}"
            append_batch(
                payment_batches,
                batch_id,
                transaction_date,
                market_code,
                f"{reservation_ref}:{receipt_ref}:LINE{line_index:04d}",
                payment_group_amount,
            )
            append_payment_output(
                output_by_payment_batch,
                batch_id,
                receipt_ref,
                reconciliation_outcome,
                payment_group_amount,
            )

            if extra_fee is not None:
                fee_batch_id = f"{payment_group_id}_fee_{line_index:04d}"
                append_batch(
                    payment_batches,
                    fee_batch_id,
                    transaction_date,
                    market_code,
                    f"{reservation_ref}:{receipt_ref}:CANCELLATION_FEE",
                    extra_fee,
                )
                append_payment_output(
                    output_by_payment_batch,
                    fee_batch_id,
                    receipt_ref,
                    reconciliation_outcome,
                    extra_fee,
                )

        if transaction_type == "Refund With Cancellation Fee":
            receipt_exceptions.append(
                {
                    "receipt_ref": receipt_ref,
                    "receipt_transaction_type": "REFUND_WITH_CANCELLATION_FEE",
                    "transaction_date": transaction_date.isoformat(),
                    "gross_amount": f"{amount:.2f}",
                    "net_amount": f"{amount - Decimal('1.25'):.2f}",
                    "your_reference": receipt_reference,
                }
            )
        if transaction_type == "Chargeback Adjustment":
            receipt_exceptions.append(
                {
                    "receipt_ref": receipt_ref,
                    "receipt_transaction_type": "CHARGEBACK",
                    "transaction_date": transaction_date.isoformat(),
                    "gross_amount": f"{amount:.2f}",
                    "net_amount": f"{amount:.2f}",
                    "your_reference": receipt_reference,
                }
            )

    def create_demo_receipt(
        receipt_ref: str,
        market_code: str,
        transaction_date: date,
        *,
        total_lines: int,
        exact_groups: list[tuple[int, str, int]],
        cfee_lines: int,
        ovp_lines: int,
        rejected_lines: int,
        chargeback_lines: int,
    ) -> None:
        contract_type = "Online Card Payment"
        totals: dict[str, dict[str, Decimal | int | None]] = {}
        cfee_payment_group_id = exact_groups[0][1]
        ovp_payment_group_id = exact_groups[-1][1]

        def track(reconciliation_outcome: str, rows: int, amount: Decimal) -> None:
            summary = totals.setdefault(reconciliation_outcome, {"rows": 0, "receipt_amount": None})
            summary["rows"] = int(summary["rows"]) + rows
            current_amount = summary["receipt_amount"]
            if current_amount is None or amount > Decimal(current_amount):
                summary["receipt_amount"] = amount

        line_index = 1
        ref_seed = int("".join(ch for ch in receipt_ref if ch.isdigit())[-5:] or "10000")

        for group_index, (count, payment_group_id, ref_prefix) in enumerate(exact_groups, start=1):
            for offset in range(count):
                reservation_ref = f"{ref_prefix + offset:010d}"
                amount = (
                    Decimal("30.00")
                    + Decimal((offset + group_index) % 80) * Decimal("1.13")
                ).quantize(Decimal("0.01"))
                add_receipt_line(
                    receipt_ref,
                    transaction_date,
                    market_code,
                    contract_type,
                    reservation_ref,
                    line_index,
                    amount,
                    "Payment",
                    reconciliation_outcome=ALLOCATION_READY,
                    payment_group_id=payment_group_id,
                )
                track(ALLOCATION_READY, 1, amount)
                line_index += 1

        fee_amount = cfee_fee(market_code)
        for offset in range(cfee_lines):
            reservation_ref = f"{1190000000 + ref_seed + offset:010d}"
            refund_batch_amount = -(
                Decimal("120.00") + Decimal(offset % 12) * Decimal("3.00")
            ).quantize(Decimal("0.01"))
            receipt_amount = (refund_batch_amount + fee_amount).quantize(Decimal("0.01"))
            add_receipt_line(
                receipt_ref,
                transaction_date,
                market_code,
                contract_type,
                reservation_ref,
                line_index,
                receipt_amount,
                "Refund With Cancellation Fee",
                reconciliation_outcome=CANCELLATION_FEE_REVIEW,
                batch_amount=refund_batch_amount,
                payment_group_id=cfee_payment_group_id,
                extra_fee=fee_amount,
            )
            track(CANCELLATION_FEE_REVIEW, 2, receipt_amount)
            line_index += 1

        for offset in range(ovp_lines):
            reservation_ref = f"{1180000000 + ref_seed + offset:010d}"
            payment_group_amount = (
                Decimal("75.00") + Decimal(offset % 30) * Decimal("2.20")
            ).quantize(Decimal("0.01"))
            receipt_amount = (payment_group_amount + Decimal("4.75")).quantize(Decimal("0.01"))
            add_receipt_line(
                receipt_ref,
                transaction_date,
                market_code,
                contract_type,
                reservation_ref,
                line_index,
                receipt_amount,
                "Payment",
                reconciliation_outcome=AMOUNT_VARIANCE_REVIEW,
                batch_amount=payment_group_amount,
                payment_group_id=ovp_payment_group_id,
            )
            track(AMOUNT_VARIANCE_REVIEW, 1, receipt_amount)
            line_index += 1

        for offset in range(rejected_lines):
            reservation_ref = f"{1170000000 + ref_seed + offset:010d}"
            amount = (Decimal("70.00") + Decimal(offset) * Decimal("8.00")).quantize(Decimal("0.01"))
            add_receipt_line(
                receipt_ref,
                transaction_date,
                market_code,
                contract_type,
                reservation_ref,
                line_index,
                amount,
                "Payment",
                status="Rejected",
            )
            line_index += 1

        for offset in range(chargeback_lines):
            reservation_ref = f"{1160000000 + ref_seed + offset:010d}"
            amount = -(Decimal("55.00") + Decimal(offset) * Decimal("6.00")).quantize(Decimal("0.01"))
            add_receipt_line(
                receipt_ref,
                transaction_date,
                market_code,
                contract_type,
                reservation_ref,
                line_index,
                amount,
                "Chargeback Adjustment",
            )
            line_index += 1

        while line_index <= total_lines:
            offset = line_index - 1
            reservation_ref = f"{1150000000 + ref_seed + offset:010d}"
            amount = (Decimal("25.00") + Decimal(offset % 50) * Decimal("1.11")).quantize(Decimal("0.01"))
            add_receipt_line(
                receipt_ref,
                transaction_date,
                market_code,
                contract_type,
                reservation_ref,
                line_index,
                amount,
                "Payment",
            )
            line_index += 1

        for status_key, summary in totals.items():
            append_receipt_output(
                output_by_receipt,
                receipt_ref,
                status_key,
                int(summary["rows"]),
                Decimal(summary["receipt_amount"]),
            )

    create_demo_receipt(
        "receipt_ref_001",
        "MKT_A",
        BASE_DATE + timedelta(days=78),
        total_lines=500,
        exact_groups=[
            (250, "payment_group_001", 1199100000),
            (80, "payment_group_002", 1199200000),
            (99, "payment_group_003", 1199300000),
        ],
        cfee_lines=20,
        ovp_lines=30,
        rejected_lines=2,
        chargeback_lines=4,
    )
    create_demo_receipt(
        "receipt_ref_002",
        "MKT_B",
        BASE_DATE + timedelta(days=79),
        total_lines=260,
        exact_groups=[
            (130, "payment_group_004", 1198100000),
            (90, "payment_group_005", 1198200000),
        ],
        cfee_lines=8,
        ovp_lines=12,
        rejected_lines=3,
        chargeback_lines=2,
    )
    create_demo_receipt(
        "receipt_ref_003",
        "MKT_C",
        BASE_DATE + timedelta(days=80),
        total_lines=180,
        exact_groups=[
            (90, "payment_group_006", 1197100000),
            (57, "payment_group_007", 1197200000),
        ],
        cfee_lines=6,
        ovp_lines=8,
        rejected_lines=2,
        chargeback_lines=2,
    )
    create_demo_receipt(
        "receipt_ref_004",
        "MKT_D",
        BASE_DATE + timedelta(days=81),
        total_lines=140,
        exact_groups=[
            (70, "payment_group_008", 1196100000),
            (41, "payment_group_009", 1196200000),
        ],
        cfee_lines=5,
        ovp_lines=6,
        rejected_lines=1,
        chargeback_lines=2,
    )

    for index, market_code in enumerate(MARKETS, start=1):
        reservation_ref, invoice_ref, _ = standard_refs(9000 + index)
        amount = (Decimal("180.00") + Decimal(index) * Decimal("11.00")).quantize(Decimal("0.01"))
        append_batch(
            payment_batches,
            f"open_payment_group_evidence_{index:03d}",
            BASE_DATE + timedelta(days=95 + index),
            market_code,
            f"{reservation_ref}:{invoice_ref}:OPEN_REVIEW",
            amount,
        )
        append_payment_output(
            output_by_payment_batch,
            f"open_payment_group_evidence_{index:03d}",
            "",
            EVIDENCE_REVIEW,
            amount,
        )

        unresolved_amount = (Decimal("95.00") + Decimal(index) * Decimal("7.00")).quantize(Decimal("0.01"))
        append_batch(
            payment_batches,
            f"open_payment_group_missing_{index:03d}",
            BASE_DATE + timedelta(days=102 + index),
            market_code,
            f"UNRESOLVED_CUSTOMER_{market_code}_{index:04d}",
            unresolved_amount,
        )
        append_payment_output(
            output_by_payment_batch,
            f"open_payment_group_missing_{index:03d}",
            "",
            MISSING_RECEIPT_EVIDENCE,
            unresolved_amount,
        )

    return payment_batches, receipts, gateway_mappings, output_by_payment_batch, output_by_receipt, receipt_exceptions


def main() -> None:
    (
        payment_batches,
        receipts,
        gateway_mappings,
        output_by_payment_batch,
        output_by_receipt,
        receipt_exceptions,
    ) = build_rows()

    write_csv(
        "sample_data/payment_batches_sample.csv",
        ["payment_batch_id", "transaction_date", "market_code", "customer", "item_description", "amount"],
        payment_batches,
    )
    write_csv(
        "sample_data/receipts_sample.csv",
        [
            "receipt_ref",
            "transaction_date",
            "market_code",
            "brand",
            "contract_type",
            "status",
            "type_of_transaction",
            "your_reference",
            "gross_amount",
            "net_amount",
        ],
        receipts,
    )
    write_csv(
        "sample_data/gateway_reference_mapping_sample.csv",
        ["gateway_token", "merchant_reference", "transaction_date", "amount", "market_code"],
        gateway_mappings,
    )
    write_csv(
        "output_examples/reconciliation_by_payment_batch.csv",
        ["payment_batch_id", "receipt_ref", "reconciliation_outcome", "row_count", "payment_batch_total"],
        sorted(output_by_payment_batch, key=lambda row: row["payment_batch_id"]),
    )
    write_csv(
        "output_examples/reconciliation_by_receipt.csv",
        ["receipt_ref", "reconciliation_outcome", "row_count", "receipt_total"],
        sorted(output_by_receipt, key=lambda row: (row["receipt_ref"], row["reconciliation_outcome"])),
    )
    write_csv(
        "output_examples/receipt_exception_classification.csv",
        ["receipt_ref", "receipt_transaction_type", "transaction_date", "gross_amount", "net_amount", "your_reference"],
        sorted(
            receipt_exceptions,
            key=lambda row: (row["receipt_ref"], row["receipt_transaction_type"], row["your_reference"]),
        ),
    )

    print(
        "Generated "
        f"{len(payment_batches)} payment batches, "
        f"{len(receipts)} receipts, "
        f"{len(gateway_mappings)} gateway mappings, "
        f"{len(receipt_exceptions)} receipt exceptions."
    )


if __name__ == "__main__":
    main()
