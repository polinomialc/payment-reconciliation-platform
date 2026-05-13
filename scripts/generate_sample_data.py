from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, time
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = ROOT / "sample_data"


PAYMENT_BATCH_COLUMNS = [
    "payment_batch_line_id",
    "payment_batch_id",
    "transaction_date",
    "market_code",
    "channel_type",
    "customer_name",
    "customer_number",
    "item_description",
    "line_total",
]

RECEIPT_COLUMNS = [
    "receipt_line_id",
    "receipt_ref",
    "transaction_date",
    "transaction_time",
    "market_code",
    "channel_type",
    "contract_type",
    "card_brand",
    "transaction_status",
    "transaction_type",
    "source_capture_method",
    "your_reference",
    "acquirer_reference",
    "gross_amount",
    "net_amount",
    "terminal_id",
]

MAPPING_COLUMNS = [
    "gateway_token",
    "merchant_reference",
    "transaction_date",
    "amount",
    "market_code",
    "source_channel",
]


@dataclass(frozen=True)
class MatchedLine:
    payment_batch_line_id: str
    payment_batch_id: str
    transaction_date: date
    market_code: str
    channel_type: str
    customer_number: str
    reservation_ref: str
    invoice_ref: str
    amount: Decimal


payment_batch_rows: list[dict[str, object]] = []
receipt_rows: list[dict[str, object]] = []
mapping_rows: list[dict[str, object]] = []
matched_lines: list[MatchedLine] = []


def money(value: Decimal) -> str:
    return f"{value:.2f}"


def write_csv(path: Path, columns: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def make_refs(sequence: int) -> tuple[str, str]:
    reservation_ref = f"12{sequence:08d}"
    invoice_ref = f"10066{sequence:07d}"
    return reservation_ref, invoice_ref


def add_payment_batch_line(
    *,
    payment_batch_id: str,
    batch_index: int,
    line_index: int,
    transaction_date: date,
    market_code: str,
    channel_type: str,
    amount: Decimal,
    sequence: int,
    matched: bool = True,
) -> MatchedLine:
    reservation_ref, invoice_ref = make_refs(sequence)
    payment_batch_line_id = f"pb{batch_index:03d}_line{line_index:03d}"
    description_suffix = "payment evidence" if matched else "pending receipt evidence"
    payment_batch_rows.append(
        {
            "payment_batch_line_id": payment_batch_line_id,
            "payment_batch_id": payment_batch_id,
            "transaction_date": transaction_date.isoformat(),
            "market_code": market_code,
            "channel_type": channel_type,
            "customer_name": "Portfolio Customer",
            "customer_number": f"CU{sequence:06d}",
            "item_description": f"RES {reservation_ref} INV {invoice_ref} {description_suffix}",
            "line_total": money(amount),
        }
    )
    line = MatchedLine(
        payment_batch_line_id=payment_batch_line_id,
        payment_batch_id=payment_batch_id,
        transaction_date=transaction_date,
        market_code=market_code,
        channel_type=channel_type,
        customer_number=f"CU{sequence:06d}",
        reservation_ref=reservation_ref,
        invoice_ref=invoice_ref,
        amount=amount,
    )
    if matched:
        matched_lines.append(line)
    return line


def add_receipt_line(
    *,
    receipt_ref: str,
    receipt_line_number: int,
    transaction_date: date,
    transaction_time: time,
    market_code: str,
    channel_type: str,
    card_brand: str,
    transaction_status: str,
    transaction_type: str,
    your_reference: str,
    amount: Decimal,
    terminal_id: str,
    acquirer_reference: str = "",
) -> None:
    receipt_rows.append(
        {
            "receipt_line_id": f"{receipt_ref}_line{receipt_line_number:03d}",
            "receipt_ref": receipt_ref,
            "transaction_date": transaction_date.isoformat(),
            "transaction_time": transaction_time.isoformat(timespec="seconds"),
            "market_code": market_code,
            "channel_type": channel_type,
            "contract_type": "E-Commerce Gateway" if channel_type == "E_COMMERCE" else "Card Present",
            "card_brand": card_brand,
            "transaction_status": transaction_status,
            "transaction_type": transaction_type,
            "source_capture_method": "PORTAL_CSV" if channel_type == "E_COMMERCE" else "TERMINAL_EXPORT",
            "your_reference": your_reference,
            "acquirer_reference": acquirer_reference,
            "gross_amount": money(amount),
            "net_amount": money(amount),
            "terminal_id": terminal_id,
        }
    )


def add_ecommerce_receipt_line(
    *,
    line: MatchedLine,
    receipt_ref: str,
    receipt_line_number: int,
    receipt_date: date,
    token_index: int,
) -> None:
    token = f"TKN{token_index:06d}"
    mapping_rows.append(
        {
            "gateway_token": token,
            "merchant_reference": line.reservation_ref,
            "transaction_date": receipt_date.isoformat(),
            "amount": money(line.amount),
            "market_code": line.market_code,
            "source_channel": "E_COMMERCE",
        }
    )
    add_receipt_line(
        receipt_ref=receipt_ref,
        receipt_line_number=receipt_line_number,
        transaction_date=receipt_date,
        transaction_time=time(9 + (receipt_line_number % 5), (receipt_line_number * 7) % 60),
        market_code=line.market_code,
        channel_type=line.channel_type,
        card_brand="VISA" if receipt_line_number % 2 else "MASTERCARD",
        transaction_status="Accepted",
        transaction_type="Payment",
        your_reference=token,
        amount=line.amount,
        terminal_id=f"WEB-{line.market_code}-01",
    )


def add_card_present_receipt_line(
    *,
    line: MatchedLine,
    receipt_ref: str,
    receipt_line_number: int,
    receipt_date: date,
    rejected: bool = False,
) -> None:
    add_receipt_line(
        receipt_ref=receipt_ref,
        receipt_line_number=receipt_line_number,
        transaction_date=receipt_date,
        transaction_time=time(10 + (receipt_line_number % 6), (receipt_line_number * 5) % 60),
        market_code=line.market_code,
        channel_type=line.channel_type,
        card_brand="VISA" if receipt_line_number % 3 else "AMEX",
        transaction_status="Rejected" if rejected else "Accepted",
        transaction_type="Payment",
        your_reference=f"RES {line.reservation_ref} INV {line.invoice_ref}",
        amount=line.amount,
        terminal_id=f"POS-{line.market_code}-01",
        acquirer_reference=f"RA{line.reservation_ref[-8:]}",
    )


def build_payment_batches() -> None:
    batch_specs = [
        ("payment_batch_001", date(2026, 4, 26), "GB", "E_COMMERCE", 25, 0),
        ("payment_batch_002", date(2026, 4, 25), "GB", "E_COMMERCE", 18, 4),
        ("payment_batch_003", date(2026, 3, 24), "DE", "CARD_PRESENT", 15, 0),
        ("payment_batch_004", date(2026, 3, 28), "GB", "CARD_PRESENT", 12, 0),
        ("payment_batch_005", date(2026, 2, 15), "ES", "CARD_PRESENT", 10, 3),
        ("payment_batch_006", date(2026, 4, 12), "DE", "E_COMMERCE", 14, 0),
        ("payment_batch_007", date(2026, 5, 2), "DE", "CARD_PRESENT", 8, 0),
        ("payment_batch_008", date(2026, 3, 10), "GB", "E_COMMERCE", 8, 2),
    ]
    amount_pattern = [
        Decimal("89.95"),
        Decimal("124.40"),
        Decimal("156.75"),
        Decimal("212.10"),
        Decimal("275.35"),
        Decimal("318.60"),
        Decimal("442.80"),
        Decimal("510.25"),
    ]

    sequence = 1001
    for batch_index, (batch_id, batch_date, market, channel, matched_count, review_count) in enumerate(batch_specs, 1):
        line_index = 1
        for _ in range(matched_count):
            base = amount_pattern[(sequence + line_index) % len(amount_pattern)]
            amount = base + Decimal(batch_index * 3 + line_index % 4)
            add_payment_batch_line(
                payment_batch_id=batch_id,
                batch_index=batch_index,
                line_index=line_index,
                transaction_date=batch_date,
                market_code=market,
                channel_type=channel,
                amount=amount,
                sequence=sequence,
                matched=True,
            )
            sequence += 1
            line_index += 1
        for _ in range(review_count):
            base = amount_pattern[(sequence + line_index) % len(amount_pattern)]
            amount = base + Decimal(batch_index * 2 + line_index % 5)
            add_payment_batch_line(
                payment_batch_id=batch_id,
                batch_index=batch_index,
                line_index=line_index,
                transaction_date=batch_date,
                market_code=market,
                channel_type=channel,
                amount=amount,
                sequence=sequence,
                matched=False,
            )
            sequence += 1
            line_index += 1


def build_receipts() -> None:
    by_batch = {}
    for line in matched_lines:
        by_batch.setdefault(line.payment_batch_id, []).append(line)

    token_index = 1

    ecommerce_plan = [
        ("receipt_ref_001", date(2026, 4, 28), by_batch["payment_batch_001"][:13]),
        ("receipt_ref_002", date(2026, 4, 27), by_batch["payment_batch_001"][13:] + by_batch["payment_batch_002"][:6]),
        ("receipt_ref_003", date(2026, 4, 25), by_batch["payment_batch_002"][6:]),
        ("receipt_ref_008", date(2026, 4, 14), by_batch["payment_batch_006"][:7]),
        ("receipt_ref_009", date(2026, 4, 13), by_batch["payment_batch_006"][7:]),
        ("receipt_ref_011", date(2026, 3, 11), by_batch["payment_batch_008"]),
    ]
    for receipt_ref, receipt_date, lines in ecommerce_plan:
        for receipt_line_number, line in enumerate(lines, 1):
            add_ecommerce_receipt_line(
                line=line,
                receipt_ref=receipt_ref,
                receipt_line_number=receipt_line_number,
                receipt_date=receipt_date,
                token_index=token_index,
            )
            token_index += 1

    card_plan = [
        ("receipt_ref_004", date(2026, 3, 24), by_batch["payment_batch_003"][:10]),
        ("receipt_ref_005", date(2026, 3, 24), by_batch["payment_batch_003"][10:]),
        ("receipt_ref_006", date(2026, 3, 28), by_batch["payment_batch_004"]),
        ("receipt_ref_007", date(2026, 2, 15), by_batch["payment_batch_005"]),
        ("receipt_ref_010", date(2026, 5, 2), by_batch["payment_batch_007"]),
    ]
    for receipt_ref, receipt_date, lines in card_plan:
        for receipt_line_number, line in enumerate(lines, 1):
            add_card_present_receipt_line(
                line=line,
                receipt_ref=receipt_ref,
                receipt_line_number=receipt_line_number,
                receipt_date=receipt_date,
                rejected=(receipt_ref == "receipt_ref_004" and receipt_line_number == 10),
            )

    add_receipt_line(
        receipt_ref="receipt_ref_003",
        receipt_line_number=99,
        transaction_date=date(2026, 4, 25),
        transaction_time=time(16, 45),
        market_code="GB",
        channel_type="E_COMMERCE",
        card_brand="VISA",
        transaction_status="Accepted",
        transaction_type="Chargeback",
        your_reference="CHARGEBACK RES 1299999001",
        amount=Decimal("-310.00"),
        terminal_id="WEB-GB-02",
    )
    add_receipt_line(
        receipt_ref="receipt_ref_011",
        receipt_line_number=99,
        transaction_date=date(2026, 3, 11),
        transaction_time=time(17, 10),
        market_code="GB",
        channel_type="E_COMMERCE",
        card_brand="MASTERCARD",
        transaction_status="Accepted",
        transaction_type="Chargeback",
        your_reference="CHARGEBACK RES 1299999002",
        amount=Decimal("-145.00"),
        terminal_id="WEB-GB-03",
    )


def main() -> None:
    build_payment_batches()
    build_receipts()

    write_csv(SAMPLE_DIR / "payment_batches_sample.csv", PAYMENT_BATCH_COLUMNS, payment_batch_rows)
    write_csv(SAMPLE_DIR / "receipts_sample.csv", RECEIPT_COLUMNS, receipt_rows)
    write_csv(SAMPLE_DIR / "gateway_reference_mapping_sample.csv", MAPPING_COLUMNS, mapping_rows)

    print(f"Wrote {len(payment_batch_rows)} payment-batch lines")
    print(f"Wrote {len(receipt_rows)} receipt lines")
    print(f"Wrote {len(mapping_rows)} gateway mapping rows")


if __name__ == "__main__":
    main()
