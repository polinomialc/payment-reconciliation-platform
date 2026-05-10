from datetime import date
from pathlib import Path
import re

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
AS_OF_DATE = pd.Timestamp(date.today())


st.set_page_config(page_title="Financial Aging Review", layout="wide")


def aging_bucket(days_open: int) -> str:
    if days_open <= 7:
        return "0-7 days"
    if days_open <= 30:
        return "8-30 days"
    if days_open <= 60:
        return "31-60 days"
    return "60+ days"


def extract_payment_reference(description: str) -> str:
    return description.split(":", maxsplit=1)[0] if ":" in description else description


def extract_gateway_token(reference: str) -> str:
    return str(reference).split()[0]


def extract_receipt_business_ref(reference: str, contract_type: str, gateway_lookup: dict[str, str]) -> str:
    if str(contract_type).upper() == "ONLINE CARD PAYMENT":
        return gateway_lookup.get(extract_gateway_token(reference), "")
    reservation_match = re.search(r"RES[: ]*([0-9]{10})", str(reference))
    if reservation_match:
        return reservation_match.group(1)
    invoice_match = re.search(r"INV[: ]*([0-9]{12})", str(reference))
    if invoice_match:
        return invoice_match.group(1)
    return str(reference)


def payment_group(payment_batch_id: str) -> str:
    return re.sub(r"_(line|fee)_\d+$", "", str(payment_batch_id))


def reference_type(description: str) -> str:
    if description.startswith("UNRESOLVED"):
        return "Unresolved"
    if "INV:" in description:
        return "Invoice / reservation"
    if ":" in description:
        return "Reservation"
    return "Unresolved"


def receipt_reference_type(reference: str, contract_type: str) -> str:
    if "CHB:" in reference or "CHARGEBACK" in reference.upper():
        return "Chargeback / adjustment"
    if "CANCELLATION_FEE" in reference.upper():
        return "Refund / cancellation fee"
    if contract_type == "Online Card Payment":
        return "Payment-channel token"
    if "INV:" in reference and "RES:" in reference:
        return "Invoice / reservation"
    if "RES:" in reference:
        return "Reservation"
    return "Unresolved"


STATUS_LABELS = {
    "Allocation Ready": "Allocation Ready",
    "Cancellation Fee Review": "Cancellation Fee Review",
    "Amount Variance Review": "Amount Variance Review",
    "Rejected Card Transaction": "Rejected Card Transaction",
    "Evidence Review Required": "Evidence Review Required",
    "Missing Receipt Evidence": "Missing Receipt Evidence",
}


@st.cache_data
def load_data(data_version: tuple[float, ...]) -> dict[str, pd.DataFrame]:
    receipts = pd.read_csv(ROOT / "sample_data" / "receipts_sample.csv", parse_dates=["transaction_date"])
    payment_batches = pd.read_csv(ROOT / "sample_data" / "payment_batches_sample.csv", parse_dates=["transaction_date"])
    gateway_mapping = pd.read_csv(ROOT / "sample_data" / "gateway_reference_mapping_sample.csv")
    by_payment_batch = pd.read_csv(ROOT / "output_examples" / "reconciliation_by_payment_batch.csv")
    by_receipt = pd.read_csv(ROOT / "output_examples" / "reconciliation_by_receipt.csv")
    receipt_exceptions = pd.read_csv(
        ROOT / "output_examples" / "receipt_exception_classification.csv",
        parse_dates=["transaction_date"],
    )
    if "receipt_ref" not in by_payment_batch.columns:
        by_payment_batch["receipt_ref"] = ""
    by_payment_batch["receipt_ref"] = by_payment_batch["receipt_ref"].fillna("")

    batch_aging = by_payment_batch.merge(payment_batches, on="payment_batch_id", how="left")
    batch_aging["payment_reference"] = batch_aging["item_description"].apply(extract_payment_reference)
    batch_aging["reference_type"] = batch_aging["item_description"].apply(reference_type)
    batch_aging["portfolio_status"] = batch_aging["reconciliation_outcome"].map(STATUS_LABELS)
    batch_aging["days_open"] = (AS_OF_DATE.normalize() - batch_aging["transaction_date"]).dt.days.clip(lower=0)
    batch_aging["aging_bucket"] = batch_aging["days_open"].apply(aging_bucket)
    allocation_statuses = {"Allocation Ready"}
    explained_statuses = {"Allocation Ready", "Cancellation Fee Review"}
    batch_aging["allocated_amount"] = batch_aging.apply(
        lambda row: row["payment_batch_total"] if row["reconciliation_outcome"] in allocation_statuses else 0,
        axis=1,
    )
    batch_aging["explained_amount"] = batch_aging.apply(
        lambda row: row["payment_batch_total"] if row["reconciliation_outcome"] in explained_statuses else 0,
        axis=1,
    )
    batch_aging["open_amount"] = batch_aging["payment_batch_total"] - batch_aging["explained_amount"]
    batch_aging["financial_status"] = batch_aging["reconciliation_outcome"].map(
        {
            "Allocation Ready": "Ready for full allocation",
            "Cancellation Fee Review": "Open - cancellation fee requires financial treatment",
            "Amount Variance Review": "Open - amount variance requires review",
            "Rejected Card Transaction": "Open - card transaction rejected by payment provider",
            "Evidence Review Required": "Open - evidence requires review",
            "Missing Receipt Evidence": "Open - missing receipt evidence",
        }
    )
    batch_aging["owner"] = batch_aging["reconciliation_outcome"].map(
        {
            "Allocation Ready": "Auto-allocation",
            "Cancellation Fee Review": "Operations",
            "Amount Variance Review": "Operations",
            "Rejected Card Transaction": "Finance",
            "Evidence Review Required": "Operations",
            "Missing Receipt Evidence": "Finance",
        }
    )
    batch_aging["next_action"] = batch_aging["reconciliation_outcome"].map(
        {
            "Allocation Ready": "Allocate matched receipt payment",
            "Cancellation Fee Review": "Review refund and cancellation-fee treatment",
            "Amount Variance Review": "Review over/under payment variance before allocation",
            "Rejected Card Transaction": "Confirm rejected card handling and keep out of allocation",
            "Evidence Review Required": "Validate invoice, reservation, or payment-channel mapping",
            "Missing Receipt Evidence": "Investigate missing receipt or operational reference",
        }
    )
    batch_aging["business_exception"] = batch_aging["reconciliation_outcome"].map(
        {
            "Allocation Ready": "None",
            "Cancellation Fee Review": "Cancellation fee",
            "Amount Variance Review": "Over/under payment",
            "Rejected Card Transaction": "Rejected card transaction",
            "Evidence Review Required": "Reference review",
            "Missing Receipt Evidence": "Missing evidence",
        }
    )

    allocation_evidence = by_receipt.merge(receipts, on="receipt_ref", how="left")
    allocation_evidence["portfolio_status"] = allocation_evidence["reconciliation_outcome"].map(STATUS_LABELS)
    receipt_exceptions["portfolio_exception"] = receipt_exceptions["receipt_transaction_type"].map(
        {
            "CHARGEBACK": "Chargeback",
            "REFUND_WITH_CANCELLATION_FEE": "Refund with cancellation fee",
            "CANCELLATION_FEE": "Cancellation fee",
            "OVER_UNDER_PAYMENT": "Amount variance",
        }
    ).fillna(receipt_exceptions["receipt_transaction_type"])
    receipts["receipt_reference_type"] = receipts.apply(
        lambda row: receipt_reference_type(str(row["your_reference"]), str(row["contract_type"])),
        axis=1,
    )

    return {
        "receipts": receipts,
        "payment_batches": payment_batches,
        "gateway_mapping": gateway_mapping,
        "by_payment_batch": by_payment_batch,
        "by_receipt": by_receipt,
        "receipt_exceptions": receipt_exceptions,
        "batch_aging": batch_aging,
        "allocation_evidence": allocation_evidence,
    }


DATA_FILES = (
    ROOT / "sample_data" / "receipts_sample.csv",
    ROOT / "sample_data" / "payment_batches_sample.csv",
    ROOT / "sample_data" / "gateway_reference_mapping_sample.csv",
    ROOT / "output_examples" / "reconciliation_by_payment_batch.csv",
    ROOT / "output_examples" / "reconciliation_by_receipt.csv",
    ROOT / "output_examples" / "receipt_exception_classification.csv",
)

data = load_data(tuple(path.stat().st_mtime for path in DATA_FILES))
batch_aging = data["batch_aging"]

page = st.sidebar.radio(
    "Demo navigation",
    ["Operations Dashboard", "Receipt Reconciliation"],
)

status_options = list(STATUS_LABELS.values())
bucket_options = ["0-7 days", "8-30 days", "31-60 days", "60+ days"]

if page == "Receipt Reconciliation":
    st.title("Receipt Reconciliation")
    st.caption(
        "Select a payment receipt and run the same kind of read-out an analyst would use: receipt lines, "
        "linked payment batches, missing-evidence transactions, and exception treatment."
    )

    receipts = data["receipts"].copy()
    receipts["receipt_total"] = receipts.groupby("receipt_ref")["gross_amount"].transform("sum")
    receipts["display_label"] = receipts["receipt_ref"]
    default_receipt = "receipt_ref_001"
    receipt_options = receipts[["receipt_ref", "display_label"]].drop_duplicates().sort_values("receipt_ref")
    receipt_refs = receipt_options["receipt_ref"].tolist()
    default_index = receipt_refs.index(default_receipt) if default_receipt in receipt_refs else 0
    selected_label = st.selectbox(
        "Receipt",
        receipt_options["display_label"].tolist(),
        index=default_index,
    )
    selected_receipt_ref = selected_label.split(" | ", maxsplit=1)[0]

    receipt_lines = receipts[receipts["receipt_ref"] == selected_receipt_ref].copy()
    receipt_lines["receipt_line"] = range(1, len(receipt_lines) + 1)
    selected_receipt = receipt_lines.iloc[0] if not receipt_lines.empty else receipts[
        receipts["receipt_ref"] == selected_receipt_ref
    ].iloc[0]
    related_batches = batch_aging[batch_aging["receipt_ref"] == selected_receipt_ref].copy()
    if not related_batches.empty:
        related_batches["payment_group_id"] = related_batches["payment_batch_id"].apply(payment_group)
    related_exception = data["receipt_exceptions"][
        data["receipt_exceptions"]["receipt_ref"] == selected_receipt_ref
    ].copy()

    gateway_lookup = dict(
        zip(
            data["gateway_mapping"]["gateway_token"].astype(str),
            data["gateway_mapping"]["merchant_reference"].astype(str),
        )
    )
    receipt_lines["mapped_reference"] = receipt_lines.apply(
        lambda row: extract_receipt_business_ref(row["your_reference"], row["contract_type"], gateway_lookup),
        axis=1,
    )

    batch_by_ref = {
        reference: rows.copy()
        for reference, rows in related_batches.groupby("payment_reference")
    } if not related_batches.empty else {}

    line_results = []
    for row in receipt_lines.itertuples(index=False):
        candidates = batch_by_ref.get(row.mapped_reference, pd.DataFrame())
        exact_candidates = candidates[
            candidates["payment_batch_total"].round(2) == round(float(row.gross_amount), 2)
        ] if not candidates.empty else pd.DataFrame()
        if "CHARGEBACK" in str(row.type_of_transaction).upper():
            outcome = "Chargeback"
            group = ""
            review_action = "Route through chargeback procedure."
        elif str(row.status).upper() == "REJECTED":
            outcome = "Rejected Card Transaction"
            group = ", ".join(sorted(candidates["payment_group_id"].unique())) if not candidates.empty else ""
            review_action = "Do not allocate; confirm rejected transaction treatment."
        elif not candidates.empty and (candidates["portfolio_status"] == "Cancellation Fee Review").any():
            outcome = "Cancellation Fee Review"
            group = ", ".join(sorted(candidates["payment_group_id"].unique()))
            review_action = "Validate refund line and cancellation fee line before treatment."
        elif not candidates.empty and (candidates["portfolio_status"] == "Amount Variance Review").any():
            outcome = "Amount Variance Review"
            group = ", ".join(sorted(candidates["payment_group_id"].unique()))
            review_action = "Review over/under payment difference."
        elif not exact_candidates.empty:
            outcome = "Allocation Ready"
            group = ", ".join(sorted(exact_candidates["payment_group_id"].unique()))
            review_action = "Allocate matched payment-group line."
        else:
            outcome = "Missing Receipt Evidence"
            group = ""
            review_action = "Investigate missing payment group line or mapping."

        line_results.append(
            {
                "Line": row.receipt_line,
                "Receipt": row.receipt_ref,
                "Date": row.transaction_date,
                "Channel": row.contract_type,
                "Provider status": row.status,
                "Transaction type": row.type_of_transaction,
                "Transaction reference": row.mapped_reference,
                "Raw reference": row.your_reference,
                "Amount": row.gross_amount,
                "Outcome": outcome,
                "Payment group": group,
                "Review action": review_action,
            }
        )

    line_detail = pd.DataFrame(line_results)
    receipt_channel = selected_receipt["contract_type"]
    receipt_market = selected_receipt["market_code"]
    lines_ready = (line_detail["Outcome"] == "Allocation Ready").sum() if not line_detail.empty else 0
    lines_review = len(line_detail) - lines_ready
    linked_payment_groups = sorted(
        {
            payment_group_name
            for value in line_detail["Payment group"].dropna().astype(str)
            for payment_group_name in value.split(", ")
            if payment_group_name
        }
    ) if not line_detail.empty else []
    missing_lines = (line_detail["Outcome"] == "Missing Receipt Evidence").sum() if not line_detail.empty else 0

    st.write(
        f"Receipt `{selected_receipt_ref}` contains `{len(receipt_lines):,}` transaction lines. "
        f"Channel: `{receipt_channel}`. Market: `{receipt_market}`."
    )

    kpi_1, kpi_2, kpi_3, kpi_4, kpi_5 = st.columns(5)
    kpi_1.metric("Receipt lines", f"{len(receipt_lines):,}")
    kpi_2.metric("Ready lines", f"{lines_ready:,}")
    kpi_3.metric("Review lines", f"{lines_review:,}")
    kpi_4.metric("Linked groups", f"{len(linked_payment_groups):,}")
    kpi_5.metric("No group", f"{missing_lines:,}")

    st.subheader("Line-Level Reconciliation")
    st.dataframe(
        line_detail[
            [
                "Line",
                "Date",
                "Channel",
                "Provider status",
                "Transaction type",
                "Transaction reference",
                "Amount",
                "Outcome",
                "Payment group",
            ]
        ],
        hide_index=True,
        use_container_width=True,
    )

    st.subheader("Reconciliation Summary")
    receipt_summary = (
        line_detail.groupby("Outcome", as_index=False)
        .agg(lines=("Line", "count"), amount=("Amount", "sum"))
        .sort_values("Outcome")
        .rename(columns={"lines": "Lines", "amount": "Receipt amount"})
    )
    st.dataframe(receipt_summary, hide_index=True, use_container_width=True)

    st.subheader("Payment Group Coverage")
    if related_batches.empty:
        st.info("No payment group lines were linked to this receipt.")
    else:
        payment_group_summary = (
            related_batches.groupby("payment_group_id", as_index=False)
            .agg(
                group_lines=("payment_batch_id", "count"),
                ready_lines=("portfolio_status", lambda values: (values == "Allocation Ready").sum()),
                cancellation_fee_lines=(
                    "portfolio_status",
                    lambda values: (values == "Cancellation Fee Review").sum(),
                ),
                variance_lines=("portfolio_status", lambda values: (values == "Amount Variance Review").sum()),
                group_amount=("payment_batch_total", "sum"),
                explained_amount=("explained_amount", "sum"),
                open_amount=("open_amount", "sum"),
            )
            .rename(
                columns={
                    "payment_group_id": "Payment group",
                    "group_lines": "Lines",
                    "ready_lines": "Ready lines",
                    "cancellation_fee_lines": "Cancellation fee lines",
                    "variance_lines": "Variance lines",
                    "group_amount": "Group amount",
                    "explained_amount": "Explained amount",
                    "open_amount": "Open amount",
                }
            )
        )
        st.dataframe(payment_group_summary, hide_index=True, use_container_width=True)

    st.subheader("Items Requiring Review")
    review_detail = line_detail[line_detail["Outcome"] != "Allocation Ready"]
    if review_detail.empty:
        st.success("All receipt lines found exact payment-group matches.")
    else:
        st.dataframe(
            review_detail[
                [
                    "Line",
                    "Transaction type",
                    "Provider status",
                    "Transaction reference",
                    "Amount",
                    "Outcome",
                    "Payment group",
                    "Review action",
                ]
            ],
            hide_index=True,
            use_container_width=True,
        )

    presentation_tab = st.tabs(["Presentation Role"])[0]
    with presentation_tab:
        st.subheader("How To Present This Page")
        st.write(
            "This page demonstrates a receipt-side reconciliation procedure. A receipt is treated as a "
            "bank/payment file containing many transaction lines. Each line is parsed, mapped to a business "
            "reference, compared against payment-group lines, and classified into allocation-ready items or "
            "operational review queues."
        )

        st.subheader("Procedure Flow")
        procedure_steps = pd.DataFrame(
            [
                {
                    "Step": "1. Parse receipt lines",
                    "Purpose": "Extract the transaction date, channel, status, transaction type, reference, and amount.",
                    "Portfolio point": "Shows that the pipeline starts from raw operational data, not a hand-built report.",
                },
                {
                    "Step": "2. Generate matching keys",
                    "Purpose": "Build comparable keys from invoice, reservation, acquirer reference, or payment-channel token.",
                    "Portfolio point": "The same model can support different departments by changing the key priority.",
                },
                {
                    "Step": "3. Match payment groups",
                    "Purpose": "Link receipt lines to payment-group lines by reference, value, sign, and date rule.",
                    "Portfolio point": "This is the core allocation evidence used by finance operations.",
                },
                {
                    "Step": "4. Classify exceptions",
                    "Purpose": "Identify chargebacks, rejected transactions, cancellation-fee cases, amount variances, and missing evidence.",
                    "Portfolio point": "Exceptions become controlled queues instead of manual spreadsheet notes.",
                },
                {
                    "Step": "5. Review and adapt",
                    "Purpose": "Expose rules as SQL blocks that can be tuned by market, channel, fee policy, or procedure.",
                    "Portfolio point": "The reconciliation framework is reusable and governed, not locked to one internal process.",
                },
            ]
        )
        st.dataframe(procedure_steps, hide_index=True, use_container_width=True)

        st.subheader("SQL Building Blocks")
        st.write("Reference parsing normalizes different receipt formats into one comparable business key.")
        st.code(
            """
case
    when contract_type = 'Online Card Payment'
        then gateway_mapping.merchant_reference
    when invoice_ref is not null
        then invoice_ref
    when reservation_ref is not null
        then reservation_ref
    else raw_reference
end as mapped_reference
            """.strip(),
            language="sql",
        )

        st.write("Exact allocation evidence is created when reference, amount, sign, and date rule agree.")
        st.code(
            """
select
    payment_group_line_id,
    receipt_ref,
    mapped_reference,
    receipt_amount,
    payment_group_amount,
    'Allocation Ready' as reconciliation_outcome
from receipt_lines r
join payment_group_lines p
  on p.mapped_reference = r.mapped_reference
 and p.amount = r.amount
 and sign(p.amount) = sign(r.amount)
 and abs(date_diff('day', p.transaction_date, r.transaction_date)) <= channel_date_tolerance
            """.strip(),
            language="sql",
        )

        st.write("Operational exceptions are layered after matching, with precedence controlled by procedure rules.")
        st.code(
            """
case
    when type_of_transaction in ('Chargeback Adjustment', 'Merchant Adjustment')
        then 'CHARGEBACK_REVIEW'
    when provider_status = 'Rejected'
        then 'REJECTED_TRANSACTION'
    when refund_amount + cancellation_fee = receipt_amount
        then 'Cancellation Fee Review'
    when same_reference = true and amount_difference <> 0
        then 'Amount Variance Review'
    when payment_group_line_id is null
        then 'Missing Receipt Evidence'
    else 'Allocation Ready'
end as reconciliation_outcome
            """.strip(),
            language="sql",
        )

        st.subheader("How It Can Be Molded")
        st.write(
            "The procedure can be adapted by changing configuration tables instead of rewriting the whole flow: "
            "date tolerance by channel, cancellation-fee amount by market, reference priority by payment method, "
            "exception precedence by procedure, and ownership of each review queue."
        )
        st.code(
            """
select * from reconciliation_rules
-- market | channel             | date_tolerance | cancellation_fee | reference_priority
-- MKT_A  | Online Card Payment | 180            | 45.00            | payment_token, reservation
-- MKT_B  | Card Present        | 0              | 50.00            | invoice, reservation, acquirer
            """.strip(),
            language="sql",
        )

        st.info(
            "Portfolio reading: this is not just a dashboard. It is a controllable reconciliation layer "
            "where raw payment evidence becomes allocation evidence, exceptions become work queues, and "
            "business rules can be maintained as documented SQL."
        )
    st.stop()

st.title("Financial Operations Aging Review")
st.caption(
    "Executive demo of payment allocation readiness, open-balance aging, and exception queues."
)

with st.expander("Dashboard filters", expanded=False):
    filter_1, filter_2, filter_3, filter_4 = st.columns([1.4, 1.1, 0.9, 0.9])
    selected_statuses = filter_1.multiselect(
        "Status",
        status_options,
        default=status_options,
        key="dashboard_status_filter_v2",
    )
    selected_buckets = filter_2.multiselect(
        "Aging bucket",
        bucket_options,
        default=bucket_options,
        key="dashboard_bucket_filter_v2",
    )
    selected_owner = filter_3.selectbox(
        "Owner",
        ["All"] + sorted(batch_aging["owner"].unique()),
        key="dashboard_owner_filter_v2",
    )
    selected_reference = filter_4.selectbox(
        "Reference type",
        ["All"] + sorted(batch_aging["reference_type"].unique()),
        key="dashboard_reference_filter_v2",
    )

filtered_aging = batch_aging[
    batch_aging["portfolio_status"].isin(selected_statuses)
    & batch_aging["aging_bucket"].isin(selected_buckets)
]
if selected_owner != "All":
    filtered_aging = filtered_aging[filtered_aging["owner"] == selected_owner]
if selected_reference != "All":
    filtered_aging = filtered_aging[filtered_aging["reference_type"] == selected_reference]

filtered_receipts = data["allocation_evidence"][
    data["allocation_evidence"]["portfolio_status"].isin(selected_statuses)
]

filtered_open = filtered_aging[filtered_aging["open_amount"] > 0]
filtered_review = filtered_aging[
    filtered_aging["portfolio_status"].isin(
        [
            "Evidence Review Required",
            "Amount Variance Review",
            "Rejected Card Transaction",
            "Missing Receipt Evidence",
        ]
    )
]
filtered_ready = filtered_aging[filtered_aging["portfolio_status"] == "Allocation Ready"]
filtered_cfee = filtered_aging[filtered_aging["portfolio_status"] == "Cancellation Fee Review"]
chargeback_count = (data["receipt_exceptions"]["receipt_transaction_type"] == "CHARGEBACK").sum()
chargeback_amount = data["receipt_exceptions"].loc[
    data["receipt_exceptions"]["receipt_transaction_type"] == "CHARGEBACK",
    "gross_amount",
].sum()

overview_kpis = st.columns(5)
overview_kpis[0].metric("Ready to allocate", f"{filtered_ready['allocated_amount'].sum():,.2f}")
overview_kpis[1].metric("Open exposure", f"{filtered_open['open_amount'].sum():,.2f}")
overview_kpis[2].metric("Open batches", f"{len(filtered_open):,}")
overview_kpis[3].metric("Operational review", f"{len(filtered_review):,}")
overview_kpis[4].metric("Chargebacks", f"{chargeback_count:,}")

tab_overview, tab_aging, tab_exceptions, tab_allocation, tab_business, tab_sources, tab_architecture = st.tabs(
    [
        "Operations Overview",
        "Aging Procedure",
        "Exception Procedure",
        "Allocation Evidence",
        "Business Context",
        "Source Data",
        "Architecture",
    ]
)

with tab_overview:
    st.subheader("Executive Snapshot")
    st.write(
        "This view separates payment batches that are ready to allocate from open balances and exceptions "
        "that require finance operations review."
    )

    left, right = st.columns([1, 1])

    with left:
        st.subheader("Allocation Readiness")
        status_summary = (
            filtered_aging.groupby("portfolio_status", as_index=False)
            .agg(
                batches=("payment_batch_id", "count"),
                total_amount=("payment_batch_total", "sum"),
                allocated_amount=("allocated_amount", "sum"),
                open_amount=("open_amount", "sum"),
            )
            .sort_values("portfolio_status")
            .rename(
                columns={
                    "portfolio_status": "Status",
                    "batches": "Batches",
                    "total_amount": "Total amount",
                    "allocated_amount": "Ready to allocate",
                    "open_amount": "Open exposure",
                }
            )
        )
        st.dataframe(status_summary, hide_index=True, use_container_width=True)

    with right:
        st.subheader("Operational Queues")
        procedure_summary = pd.DataFrame(
            [
                {
                    "Procedure": "Allocation",
                    "Purpose": "Receipt evidence is complete.",
                    "Items": len(filtered_ready),
                    "Exposure": filtered_ready["allocated_amount"].sum(),
                },
                {
                    "Procedure": "Cancellation fee review",
                    "Purpose": "Refund and retained cancellation fee require treatment.",
                    "Items": len(filtered_cfee),
                    "Exposure": filtered_cfee["payment_batch_total"].sum(),
                },
                {
                    "Procedure": "Open-balance aging",
                    "Purpose": "Unresolved batches remain open by aging bucket.",
                    "Items": len(filtered_open),
                    "Exposure": filtered_open["open_amount"].sum(),
                },
                {
                    "Procedure": "Receipt exceptions",
                    "Purpose": "Chargebacks and refund exceptions are tracked separately.",
                    "Items": len(data["receipt_exceptions"]),
                    "Exposure": abs(data["receipt_exceptions"]["gross_amount"].sum()),
                },
            ]
        )
        st.dataframe(procedure_summary, hide_index=True, use_container_width=True)

    st.subheader("Aging Exposure")
    overview_aging = filtered_open.groupby("aging_bucket", as_index=False).agg(
        open_exposure=("open_amount", "sum"),
        batches=("payment_batch_id", "count"),
    )
    st.dataframe(
        overview_aging.rename(
            columns={
                "aging_bucket": "Aging bucket",
                "open_exposure": "Open exposure",
                "batches": "Batches",
            }
        ),
        hide_index=True,
        use_container_width=True,
    )

with tab_aging:
    st.subheader("Open Balance Aging")
    aging_amount = (
        filtered_open.pivot_table(
            index="aging_bucket",
            columns="portfolio_status",
            values="open_amount",
            aggfunc="sum",
            fill_value=0,
        )
        .reindex(bucket_options, fill_value=0)
        .reset_index()
        .rename(columns={"aging_bucket": "Aging bucket"})
    )
    aging_count = (
        filtered_open.pivot_table(
            index="aging_bucket",
            columns="portfolio_status",
            values="payment_batch_id",
            aggfunc="count",
            fill_value=0,
        )
        .reindex(bucket_options, fill_value=0)
        .reset_index()
        .rename(columns={"aging_bucket": "Aging bucket"})
    )
    aging_left, aging_right = st.columns(2)
    aging_left.dataframe(aging_amount, hide_index=True, use_container_width=True)
    aging_right.dataframe(aging_count, hide_index=True, use_container_width=True)

    st.subheader("Aging Work Queue")
    st.dataframe(
        filtered_open[
            [
                "payment_batch_id",
                "receipt_ref",
                "payment_reference",
                "reference_type",
                "transaction_date",
                "days_open",
                "aging_bucket",
                "portfolio_status",
                "business_exception",
                "payment_batch_total",
                "open_amount",
                "owner",
                "next_action",
            ]
        ],
        hide_index=True,
        use_container_width=True,
    )

with tab_exceptions:
    exception_kpis = st.columns(4)
    exception_kpis[0].metric(
        "Amount variances",
        f"{(filtered_aging['portfolio_status'] == 'Amount Variance Review').sum():,}",
    )
    exception_kpis[1].metric(
        "Rejected cards",
        f"{(filtered_aging['portfolio_status'] == 'Rejected Card Transaction').sum():,}",
    )
    exception_kpis[2].metric("Cancellation fee items", f"{len(filtered_cfee):,}")
    exception_kpis[3].metric("Chargebacks", f"{chargeback_count:,}", f"{chargeback_amount:,.2f}")

    st.subheader("Batch Exceptions")
    batch_exceptions = filtered_aging[
        filtered_aging["portfolio_status"].isin(
            [
                "Amount Variance Review",
                "Rejected Card Transaction",
                "Cancellation Fee Review",
                "Evidence Review Required",
            ]
        )
    ]
    st.dataframe(
        batch_exceptions[
            [
                "payment_batch_id",
                "receipt_ref",
                "payment_reference",
                "reference_type",
                "portfolio_status",
                "business_exception",
                "transaction_date",
                "payment_batch_total",
                "open_amount",
                "owner",
                "next_action",
            ]
        ],
        hide_index=True,
        use_container_width=True,
    )

    st.subheader("Receipt Exceptions")
    st.dataframe(
        data["receipt_exceptions"][
            [
                "receipt_ref",
                "portfolio_exception",
                "transaction_date",
                "gross_amount",
                "net_amount",
                "your_reference",
            ]
        ],
        hide_index=True,
        use_container_width=True,
    )

with tab_allocation:
    st.subheader("Allocation Evidence")
    st.dataframe(
        filtered_receipts[
            [
                "receipt_ref",
                "transaction_date",
                "your_reference",
                "portfolio_status",
                "gross_amount",
                "receipt_total",
                "contract_type",
            ]
        ],
        hide_index=True,
        use_container_width=True,
    )

    st.subheader("Allocation Rule")
    st.info(
        "A payment batch is ready for full allocation only when the payment receipt evidence matches the "
        "invoice or reservation reference, amount, sign, and date rule. Review items remain open until "
        "the operational owner confirms the variance, rejection, or payment-channel mapping."
    )

with tab_business:
    st.subheader("Business Concepts")
    st.table(
        pd.DataFrame(
            [
                {
                    "Concept": "Invoice reference",
                    "Operational meaning": "Financial document reference used for accounting allocation.",
                    "SQL signal": "INV",
                },
                {
                    "Concept": "Reservation reference",
                    "Operational meaning": "Rental booking reference used when the payment relates to a car-rental reservation.",
                    "SQL signal": "RES",
                },
                {
                    "Concept": "Payment channel",
                    "Operational meaning": "Route used to process the customer transaction; e-commerce is one channel.",
                    "SQL signal": "contract_type / mapping token",
                },
                {
                    "Concept": "Receipt",
                    "Operational meaning": "External payment evidence from the payment provider or banking side.",
                    "SQL signal": "receipt_ref",
                },
                {
                    "Concept": "Payment batch",
                    "Operational meaning": "Internal grouped payment object that needs allocation or review.",
                    "SQL signal": "payment_batch_id",
                },
            ]
        )
    )

    st.subheader("Exception Meanings")
    st.table(
        pd.DataFrame(
            [
                {
                    "Status": "Rejected Card Transaction",
                    "Business meaning": "Customer card transaction was attempted but rejected by the bank, acquirer, or payment provider.",
                    "Operational treatment": "Keep out of standard allocation and check whether a later successful payment exists.",
                },
                {
                    "Status": "Cancellation Fee Review",
                    "Business meaning": "Cancellation fee charged to the customer after a reservation cancellation.",
                    "Operational treatment": "Treat refund and retained fee together, then allocate according to cancellation-fee policy.",
                },
                {
                    "Status": "Amount Variance Review",
                    "Business meaning": "Payment was processed above or below the expected amount.",
                    "Operational treatment": "Review the variance before allocation.",
                },
                {
                    "Status": "Chargeback",
                    "Business meaning": "Dispute, reversal, or payment adjustment after the original transaction.",
                    "Operational treatment": "Route to exception handling and report separately from normal payment allocation.",
                },
            ]
        )
    )

with tab_sources:
    source_tab_1, source_tab_2, source_tab_3, source_tab_4 = st.tabs(
        ["Payment Receipts", "Payment Batches", "Payment-Channel Mapping", "Published Outputs"]
    )

    with source_tab_1:
        st.dataframe(data["receipts"], hide_index=True, use_container_width=True)

    with source_tab_2:
        st.dataframe(data["payment_batches"], hide_index=True, use_container_width=True)

    with source_tab_3:
        st.dataframe(data["gateway_mapping"], hide_index=True, use_container_width=True)

    with source_tab_4:
        left, right = st.columns(2)
        left.dataframe(data["by_payment_batch"], hide_index=True, use_container_width=True)
        right.dataframe(data["by_receipt"], hide_index=True, use_container_width=True)

with tab_architecture:
    st.subheader("Aging-Centered Operating Model")
    model_1, model_2, model_3, model_4 = st.columns(4)
    model_1.info("Payment receipts provide external evidence from payment channels.")
    model_2.info("Payment batches are the internal allocation object.")
    model_3.info("Invoice and reservation references connect receipts to expected payments.")
    model_4.info("Open batches, rejected transactions, and variances drive the aging queue.")

    st.subheader("Rule Coverage Demonstrated")
    st.table(
        pd.DataFrame(
            [
                {"Rule area": "Receipt-to-batch reference matching", "Layer": "SQL", "Demo status": "Included"},
                {"Rule area": "Same amount and date validation", "Layer": "SQL", "Demo status": "Included"},
                {"Rule area": "Payment-channel token matching", "Layer": "SQL", "Demo status": "Included"},
                {"Rule area": "Cancellation-fee pairing", "Layer": "SQL", "Demo status": "Included"},
                {"Rule area": "Over/under-payment detection", "Layer": "SQL", "Demo status": "Included"},
                {"Rule area": "Rejected card transaction override", "Layer": "SQL", "Demo status": "Included"},
                {"Rule area": "Chargeback classification", "Layer": "SQL + operations", "Demo status": "Included"},
                {"Rule area": "Open payment-batch aging", "Layer": "Streamlit", "Demo status": "Included"},
            ]
        )
    )
