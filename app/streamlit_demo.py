from __future__ import annotations

from pathlib import Path
from time import perf_counter

import duckdb
import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]


st.set_page_config(page_title="Payment Reconciliation Platform", layout="wide")


@st.cache_resource(show_spinner=False)
def build_runtime_engine() -> dict[str, object]:
    start = perf_counter()
    connection = duckdb.connect(database=":memory:")
    connection.execute("set preserve_insertion_order=false;")
    connection.execute("set threads=1;")
    connection.execute(
        f"""
        create table raw_payment_batches as
        select * from read_csv_auto('{(ROOT / "sample_data/payment_batches_sample.csv").as_posix()}', header=true);

        create table raw_receipts as
        select * from read_csv_auto('{(ROOT / "sample_data/receipts_sample.csv").as_posix()}', header=true);

        create table raw_gateway_reference_mapping as
        select * from read_csv_auto('{(ROOT / "sample_data/gateway_reference_mapping_sample.csv").as_posix()}', header=true);
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

    return {
        "connection": connection,
        "build_seconds": round(perf_counter() - start, 3),
    }


@st.cache_data(show_spinner=False)
def load_runtime_snapshot() -> dict[str, object]:
    start = perf_counter()
    connection = build_runtime_engine()["connection"]

    snapshot = {
        "payment_batch_summary": connection.sql(
            """
            select *
            from reconciliation_by_payment_batch
            order by transaction_date, payment_batch_id
            """
        ).df(),
        "payment_batch_lines": connection.sql(
            """
            select *
            from reconciled_payment_batch_lines
            order by transaction_date, payment_batch_id, payment_batch_line_id
            """
        ).df(),
        "payment_batch_receipt_summary": connection.sql(
            """
            select *
            from payment_batch_receipt_summary
            order by transaction_date, payment_batch_id, reconciliation_target
            """
        ).df(),
        "receipt_summary": connection.sql(
            """
            select *
            from reconciliation_by_receipt
            order by transaction_date, receipt_ref
            """
        ).df(),
        "receipt_lines": connection.sql(
            """
            select *
            from reconciled_receipt_lines
            order by transaction_date, receipt_ref, receipt_line_id
            """
        ).df(),
        "receipt_payment_batch_summary": connection.sql(
            """
            select *
            from receipt_payment_batch_summary
            order by transaction_date, receipt_ref, payment_batch_id
            """
        ).df(),
        "runtime_summary": connection.sql(
            """
            select *
            from reconciliation_runtime_summary
            order by object_name
            """
        ).df(),
        "raw_payment_batches": connection.sql(
            """
            select *
            from raw_payment_batches
            order by transaction_date, payment_batch_id, payment_batch_line_id
            """
        ).df(),
        "raw_receipts": connection.sql(
            """
            select *
            from raw_receipts
            order by transaction_date, receipt_ref, receipt_line_id
            """
        ).df(),
        "raw_gateway_reference_mapping": connection.sql(
            """
            select *
            from raw_gateway_reference_mapping
            order by transaction_date, gateway_token
            """
        ).df(),
    }
    snapshot["query_seconds"] = round(perf_counter() - start, 3)
    return snapshot


def money(value: float | int | None) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "0.00"
    return f"{float(value):,.2f}"


def pct(numerator: float, denominator: float) -> str:
    if not denominator:
        return "0.0%"
    return f"{100 * float(numerator) / float(denominator):.1f}%"


def prettify_channel(value: object) -> object:
    mapping = {
        "E_COMMERCE": "E-commerce",
        "CARD_PRESENT": "Card Present",
    }
    return mapping.get(value, value)


def prettify_outcome(value: object) -> object:
    mapping = {
        "MATCHED_TO_RECEIPTS": "Matched to receipts",
        "LINKED_TO_PAYMENT_BATCHES": "Linked to payment batches",
        "REJECTED_RECEIPT": "Rejected transaction",
        "CHARGEBACK": "Chargeback",
        "CHECK": "Review",
        "REJECTED": "Rejected transaction",
        "UNLINKED_RECEIPT": "Unlinked receipt",
    }
    return mapping.get(value, value)


def prettify_status_token(value: object) -> object:
    mapping = {
        "MATCH": "Matched",
        "CHECK": "Review",
        "MISSING_REFERENCE": "Review",
        "REJECTED": "Rejected transaction",
        "CHARGEBACK": "Chargeback",
        "UNLINKED": "Unlinked receipt",
        "REJECTED_CARD_TRANSACTION": "Rejected transaction",
    }
    return mapping.get(value, value)


def prettify_composite_value(value: object) -> object:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return value
    text = str(value)
    if "," not in text:
        return prettify_status_token(text)
    return ", ".join(prettify_status_token(part.strip()) for part in text.split(","))


def format_display_frame(
    df: pd.DataFrame,
    channel_columns: list[str] | None = None,
    outcome_columns: list[str] | None = None,
    status_columns: list[str] | None = None,
    target_columns: list[str] | None = None,
) -> pd.DataFrame:
    result = df.copy()
    for column in result.columns:
        if pd.api.types.is_datetime64_any_dtype(result[column]):
            result[column] = result[column].dt.strftime("%Y-%m-%d")
        elif "date" in column.lower():
            parsed = pd.to_datetime(result[column], errors="coerce")
            if parsed.notna().any():
                result[column] = parsed.dt.strftime("%Y-%m-%d").fillna(result[column])
        elif pd.api.types.is_float_dtype(result[column]):
            result[column] = result[column].round(2)
    for column in channel_columns or []:
        if column in result.columns:
            result[column] = result[column].map(prettify_channel)
    for column in outcome_columns or []:
        if column in result.columns:
            result[column] = result[column].map(prettify_outcome)
    for column in status_columns or []:
        if column in result.columns:
            result[column] = result[column].map(prettify_composite_value)
    for column in target_columns or []:
        if column in result.columns:
            result[column] = result[column].map(prettify_status_token)
    return result.where(pd.notna(result), "")


def apply_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #f4f7fb;
            --panel: #ffffff;
            --border: #d9e2ec;
            --text: #142033;
            --muted: #667085;
            --accent: #0b6f92;
        }

        .stApp {
            background:
                radial-gradient(circle at top right, rgba(11, 111, 146, 0.12), transparent 28%),
                linear-gradient(180deg, #f4f7fb 0%, #eef3f8 100%);
        }

        .block-container {
            max-width: 1420px;
            padding-top: 1.3rem;
            padding-bottom: 2.8rem;
        }

        .hero-shell {
            background: linear-gradient(135deg, #0f2745 0%, #124d6f 58%, #1d6f87 100%);
            border-radius: 22px;
            padding: 1.55rem 1.65rem;
            color: #ffffff;
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 18px 35px rgba(15, 39, 69, 0.16);
            margin-bottom: 1.1rem;
        }

        .hero-kicker {
            font-size: 0.8rem;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            opacity: 0.82;
            margin-bottom: 0.35rem;
            font-weight: 700;
        }

        .hero-title {
            font-size: 2.25rem;
            line-height: 1.04;
            font-weight: 700;
            margin: 0 0 0.45rem;
        }

        .hero-copy {
            font-size: 1rem;
            line-height: 1.52;
            color: rgba(255, 255, 255, 0.85);
            max-width: 940px;
            margin: 0 0 0.95rem;
        }

        .pill-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }

        .pill {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 0.42rem 0.72rem;
            background: rgba(255, 255, 255, 0.13);
            border: 1px solid rgba(255, 255, 255, 0.14);
            font-size: 0.84rem;
        }

        .metric-card {
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1rem 1rem 1.05rem;
            min-height: 120px;
            box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
        }

        .metric-label {
            color: var(--muted);
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.45rem;
        }

        .metric-value {
            color: var(--text);
            font-size: 1.82rem;
            line-height: 1.05;
            font-weight: 700;
        }

        .metric-sub {
            color: var(--muted);
            font-size: 0.88rem;
            margin-top: 0.38rem;
            line-height: 1.4;
        }

        .callout {
            background: var(--panel);
            border: 1px solid var(--border);
            border-left: 4px solid var(--accent);
            border-radius: 14px;
            padding: 0.9rem 1rem;
            color: var(--text);
            box-shadow: 0 2px 10px rgba(15, 23, 42, 0.03);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_metric(label: str, value: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-sub">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def hero(build_seconds: float, query_seconds: float) -> None:
    st.markdown(
        f"""
        <div class="hero-shell">
            <div class="hero-kicker">Sanitized Runtime Demo</div>
            <div class="hero-title">Payment Reconciliation Platform</div>
            <p class="hero-copy">
                This app runs the reconciliation flow live in DuckDB over a compact public sample.
                The focus is direct operational reading: each payment batch shows the receipts or open
                queue it lands on, and each receipt shows the payment batches, chargebacks, or rejected
                transactions it carries.
            </p>
            <div class="pill-row">
                <span class="pill">Live SQL runtime</span>
                <span class="pill">Compact public sample</span>
                <span class="pill">Direct payment-batch-to-receipt reading</span>
                <span class="pill">Channels: E-commerce / Card Present</span>
                <span class="pill">Engine build: {build_seconds:.3f}s</span>
                <span class="pill">Snapshot load: {query_seconds:.3f}s</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def prepare_batch_summary(df: pd.DataFrame) -> pd.DataFrame:
    result = df.rename(
        columns={
            "payment_batch_id": "Payment Batch",
            "transaction_date": "Transaction Date",
            "channel_type": "Channel",
            "payment_batch_total": "Batch Total",
            "linked_receipt_total": "Linked Amount",
            "open_line_total": "Review Amount",
            "reconciliation_outcome": "Outcome",
        }
    ).copy()
    return result[
        [
            "Payment Batch",
            "Transaction Date",
            "Channel",
            "Batch Total",
            "Linked Amount",
            "Review Amount",
            "Outcome",
        ]
    ]


def prepare_batch_grid(batch_summary: pd.DataFrame, batch_target_summary: pd.DataFrame) -> pd.DataFrame:
    meta = batch_summary[["payment_batch_id", "reconciliation_outcome"]].copy()
    grid = batch_target_summary.merge(meta, on="payment_batch_id", how="left")
    return grid.rename(
        columns={
            "payment_batch_id": "Payment Batch",
            "transaction_date": "Transaction Date",
            "channel_type": "Channel",
            "payment_batch_total": "Batch Total",
            "reconciliation_target": "Receipt / Queue",
            "linked_amount": "Amount",
            "line_count": "Lines",
            "line_statuses": "Line Status",
            "reconciliation_outcome": "Overall Outcome",
        }
    )[
        [
            "Payment Batch",
            "Transaction Date",
            "Channel",
            "Batch Total",
            "Receipt / Queue",
            "Amount",
            "Lines",
            "Line Status",
            "Overall Outcome",
        ]
    ]


def prepare_batch_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    result = df.rename(
        columns={
            "reconciliation_target": "Receipt / Queue",
            "linked_amount": "Amount",
            "line_count": "Lines",
            "line_statuses": "Line Status",
        }
    )[
        [
            "Receipt / Queue",
            "Amount",
            "Lines",
            "Line Status",
        ]
    ].copy()
    total_row = pd.DataFrame(
        [
            {
                "Receipt / Queue": "Grand Total",
                "Amount": result["Amount"].sum(),
                "Lines": result["Lines"].sum(),
                "Line Status": "",
            }
        ]
    )
    return pd.concat([result, total_row], ignore_index=True)


def prepare_batch_lines(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy().reset_index(drop=True)
    result.insert(0, "Line", [f"Line {i}" for i in range(1, len(result) + 1)])
    result["Receipt / Queue"] = result["reconciliation_target"]
    return result.rename(
        columns={
            "transaction_date": "Transaction Date",
            "line_total": "Line Total",
            "match_status": "Status",
            "item_description": "Description",
            "invoice_ref": "Invoice",
            "reservation_ref": "Reservation",
            "match_rule": "Match Rule",
        }
    )[
        [
            "Line",
            "Transaction Date",
            "Receipt / Queue",
            "Line Total",
            "Status",
            "Invoice",
            "Reservation",
            "Match Rule",
            "Description",
        ]
    ]


def prepare_receipt_summary(df: pd.DataFrame) -> pd.DataFrame:
    result = df.rename(
        columns={
            "receipt_ref": "Receipt",
            "transaction_date": "Transaction Date",
            "channel_type": "Channel",
            "receipt_total": "Receipt Total",
            "reconciliation_outcome": "Outcome",
        }
    ).copy()
    return result[
        [
            "Receipt",
            "Transaction Date",
            "Channel",
            "Receipt Total",
            "Outcome",
        ]
    ]


def prepare_receipt_grid(receipt_summary: pd.DataFrame, receipt_target_summary: pd.DataFrame) -> pd.DataFrame:
    meta = receipt_summary[["receipt_ref", "receipt_total", "reconciliation_outcome"]].copy()
    grid = receipt_target_summary.merge(meta, on="receipt_ref", how="left")
    return grid.rename(
        columns={
            "receipt_ref": "Receipt",
            "transaction_date": "Transaction Date",
            "channel_type": "Channel",
            "receipt_total": "Receipt Total",
            "payment_batch_id": "Payment Batch / Queue",
            "linked_amount": "Amount",
            "line_count": "Lines",
            "line_statuses": "Line Status",
            "reconciliation_outcome": "Overall Outcome",
        }
    )[
        [
            "Receipt",
            "Transaction Date",
            "Channel",
            "Receipt Total",
            "Payment Batch / Queue",
            "Amount",
            "Lines",
            "Line Status",
            "Overall Outcome",
        ]
    ]


def prepare_receipt_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    result = df.rename(
        columns={
            "payment_batch_id": "Payment Batch / Queue",
            "linked_amount": "Amount",
            "line_count": "Lines",
            "line_statuses": "Line Status",
        }
    )[
        [
            "Payment Batch / Queue",
            "Amount",
            "Lines",
            "Line Status",
        ]
    ].copy()
    total_row = pd.DataFrame(
        [
            {
                "Payment Batch / Queue": "Grand Total",
                "Amount": result["Amount"].sum(),
                "Lines": result["Lines"].sum(),
                "Line Status": "",
            }
        ]
    )
    return pd.concat([result, total_row], ignore_index=True)


def prepare_receipt_lines(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy().reset_index(drop=True)
    result.insert(0, "Line", [f"Line {i}" for i in range(1, len(result) + 1)])
    result["Payment Batch / Queue"] = result["linked_payment_batches"].fillna("")
    result["Payment Batch / Queue"] = result["Payment Batch / Queue"].replace("", "UNLINKED")
    return result.rename(
        columns={
            "transaction_date": "Transaction Date",
            "transaction_status": "Transaction Status",
            "transaction_type": "Transaction Type",
            "your_reference": "Payment Reference",
            "gross_amount": "Gross Amount",
            "linked_statuses": "Linked Status",
            "receipt_exception_type": "Receipt Exception",
            "invoice_ref": "Invoice",
            "reservation_ref": "Reservation",
        }
    )[
        [
            "Line",
            "Transaction Date",
            "Transaction Status",
            "Transaction Type",
            "Payment Batch / Queue",
            "Gross Amount",
            "Linked Status",
            "Receipt Exception",
            "Payment Reference",
            "Invoice",
            "Reservation",
        ]
    ]


def prepare_source_payment_batches(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(
        columns={
            "payment_batch_line_id": "Payment Batch Line",
            "payment_batch_id": "Payment Batch",
            "transaction_date": "Transaction Date",
            "market_code": "Market",
            "channel_type": "Channel",
            "customer_number": "Customer",
            "item_description": "Source Description",
            "line_total": "Amount",
        }
    )[
        [
            "Payment Batch Line",
            "Payment Batch",
            "Transaction Date",
            "Market",
            "Channel",
            "Customer",
            "Source Description",
            "Amount",
        ]
    ]


def prepare_source_receipts(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(
        columns={
            "receipt_line_id": "Receipt Line",
            "receipt_ref": "Receipt",
            "transaction_date": "Transaction Date",
            "transaction_time": "Time",
            "market_code": "Market",
            "channel_type": "Channel",
            "transaction_status": "Provider Status",
            "transaction_type": "Transaction Type",
            "your_reference": "Provider Reference",
            "gross_amount": "Gross Amount",
            "terminal_id": "Terminal",
        }
    )[
        [
            "Receipt Line",
            "Receipt",
            "Transaction Date",
            "Time",
            "Market",
            "Channel",
            "Provider Status",
            "Transaction Type",
            "Provider Reference",
            "Gross Amount",
            "Terminal",
        ]
    ]


def prepare_source_mapping(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(
        columns={
            "gateway_token": "Gateway Token",
            "merchant_reference": "Business Reference",
            "transaction_date": "Transaction Date",
            "amount": "Amount",
            "market_code": "Market",
            "source_channel": "Source Channel",
        }
    )[
        [
            "Gateway Token",
            "Business Reference",
            "Transaction Date",
            "Amount",
            "Market",
            "Source Channel",
        ]
    ]


def describe_distribution(name: str, total_amount: float, breakdown_df: pd.DataFrame) -> str:
    parts = []
    for _, row in breakdown_df.iterrows():
        target_column = breakdown_df.columns[0]
        if row[target_column] == "Grand Total":
            continue
        parts.append(f"{row[target_column]} {money(row['Amount'])}")
    if not parts:
        return f"{name} total {money(total_amount)} has no linked targets."
    if len(parts) == 1:
        detail = parts[0]
    else:
        detail = ", ".join(parts[:-1]) + f", and {parts[-1]}"
    return f"{name} total {money(total_amount)} is split across {detail}."


def main() -> None:
    apply_styles()

    runtime = load_runtime_snapshot()
    engine = build_runtime_engine()
    query_receipt = st.query_params.get("receipt")

    payment_batch_summary = runtime["payment_batch_summary"].copy()
    payment_batch_lines = runtime["payment_batch_lines"].copy()
    payment_batch_receipt_summary = runtime["payment_batch_receipt_summary"].copy()
    receipt_summary = runtime["receipt_summary"].copy()
    receipt_lines = runtime["receipt_lines"].copy()
    receipt_payment_batch_summary = runtime["receipt_payment_batch_summary"].copy()
    runtime_summary = runtime["runtime_summary"].copy()
    raw_payment_batches = runtime["raw_payment_batches"].copy()
    raw_receipts = runtime["raw_receipts"].copy()
    raw_gateway_reference_mapping = runtime["raw_gateway_reference_mapping"].copy()

    hero(float(engine["build_seconds"]), float(runtime["query_seconds"]))

    scope_choice = st.radio(
        "Channel scope",
        ["All", "E-commerce", "Card Present"],
        horizontal=True,
    )
    scope_map = {
        "All": None,
        "E-commerce": "E_COMMERCE",
        "Card Present": "CARD_PRESENT",
    }
    selected_channel = scope_map[scope_choice]

    if selected_channel:
        payment_batch_summary = payment_batch_summary[payment_batch_summary["channel_type"] == selected_channel].copy()
        payment_batch_lines = payment_batch_lines[payment_batch_lines["channel_type"] == selected_channel].copy()
        payment_batch_receipt_summary = payment_batch_receipt_summary[
            payment_batch_receipt_summary["channel_type"] == selected_channel
        ].copy()
        receipt_summary = receipt_summary[receipt_summary["channel_type"] == selected_channel].copy()
        receipt_lines = receipt_lines[receipt_lines["channel_type"] == selected_channel].copy()
        receipt_payment_batch_summary = receipt_payment_batch_summary[
            receipt_payment_batch_summary["channel_type"] == selected_channel
        ].copy()
        raw_payment_batches = raw_payment_batches[raw_payment_batches["channel_type"] == selected_channel].copy()
        raw_receipts = raw_receipts[raw_receipts["channel_type"] == selected_channel].copy()
        raw_gateway_reference_mapping = raw_gateway_reference_mapping[
            raw_gateway_reference_mapping["source_channel"] == selected_channel
        ].copy()

    total_lines = len(payment_batch_lines)
    matched_lines = int((payment_batch_lines["match_status"] == "MATCH").sum())
    matched_amount = float(payment_batch_lines.loc[payment_batch_lines["match_status"] == "MATCH", "line_total"].sum())
    open_amount = float(
        payment_batch_lines.loc[
            payment_batch_lines["match_status"].isin(["CHECK", "MISSING_REFERENCE"]),
            "line_total",
        ].sum()
    )
    open_line_count = int(payment_batch_lines["match_status"].isin(["CHECK", "MISSING_REFERENCE"]).sum())

    metric_1, metric_2, metric_3, metric_4 = st.columns(4)
    with metric_1:
        render_metric(
            "Payment Batches",
            str(payment_batch_summary["payment_batch_id"].nunique()),
            "Compact sample shaped for direct operational reading.",
        )
    with metric_2:
        render_metric(
            "Receipts",
            str(receipt_summary["receipt_ref"].nunique()),
            "Each receipt belongs to a single payment channel.",
        )
    with metric_3:
        render_metric(
            "Matched Amount",
            money(matched_amount),
            f"Line match rate {pct(matched_lines, total_lines)}",
        )
    with metric_4:
        render_metric(
            "Review Amount",
            money(open_amount),
            f"{open_line_count} lines still remain in review.",
        )

    st.markdown(
        """
        <div class="callout">
            <strong>Reading model:</strong> the reconciliation views are split by target. If one payment batch links
            to two receipts and one review queue, it shows three rows. The receipt view follows the same rule in the
            opposite direction.
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_overview, tab_batches, tab_receipts, tab_source, tab_runtime = st.tabs(
        [
            "Overview",
            "Reconciliation by Payment Batch",
            "Reconciliation by Receipt",
            "Source Evidence",
            "Runtime and SQL",
        ]
    )

    with tab_overview:
        st.subheader("Operational snapshot")
        st.caption("Compact public sample, direct reading, live SQL output.")

        left, right = st.columns(2)
        with left:
            st.markdown("**Payment batch snapshot**")
            st.dataframe(
                format_display_frame(
                    prepare_batch_summary(payment_batch_summary),
                    channel_columns=["Channel"],
                    outcome_columns=["Outcome"],
                    target_columns=["Outcome"],
                ),
                use_container_width=True,
                hide_index=True,
            )
        with right:
            st.markdown("**Receipt snapshot**")
            st.dataframe(
                format_display_frame(
                    prepare_receipt_summary(receipt_summary),
                    channel_columns=["Channel"],
                    outcome_columns=["Outcome"],
                ),
                use_container_width=True,
                hide_index=True,
            )

    with tab_batches:
        st.subheader("Reconciliation by payment batch")
        st.caption("Each row shows one payment-batch target: a linked receipt or the review queue.")
        st.dataframe(
            format_display_frame(
                prepare_batch_grid(payment_batch_summary, payment_batch_receipt_summary),
                channel_columns=["Channel"],
                outcome_columns=["Overall Outcome"],
                status_columns=["Line Status"],
                target_columns=["Receipt / Queue"],
            ),
            use_container_width=True,
            hide_index=True,
        )

        batch_options = payment_batch_summary["payment_batch_id"].tolist()
        if batch_options:
            selected_batch = st.selectbox("Select payment batch", batch_options, index=0)
            batch_row = payment_batch_summary[payment_batch_summary["payment_batch_id"] == selected_batch].iloc[0]
            batch_breakdown_raw = payment_batch_receipt_summary[
                payment_batch_receipt_summary["payment_batch_id"] == selected_batch
            ].copy()
            batch_breakdown = prepare_batch_breakdown(batch_breakdown_raw)
            batch_detail = payment_batch_lines[payment_batch_lines["payment_batch_id"] == selected_batch].copy()

            b1, b2, b3, b4 = st.columns(4)
            with b1:
                render_metric("Payment Batch", selected_batch, "Compact public identifier.")
            with b2:
                render_metric("Batch Total", money(batch_row["payment_batch_total"]), "Sum of all lines in this payment batch.")
            with b3:
                render_metric("Linked Amount", money(batch_row["linked_receipt_total"]), "Amount already tied to receipts.")
            with b4:
                render_metric("Review Amount", money(batch_row["open_line_total"]), "Amount still sitting in review.")

            st.caption(describe_distribution(selected_batch, float(batch_row["payment_batch_total"]), batch_breakdown))

            st.markdown("**Receipt / queue breakdown**")
            st.dataframe(
                format_display_frame(
                    batch_breakdown,
                    status_columns=["Line Status"],
                    target_columns=["Receipt / Queue"],
                ),
                use_container_width=True,
                hide_index=True,
            )

            st.markdown("**Line detail**")
            st.dataframe(
                format_display_frame(
                    prepare_batch_lines(batch_detail),
                    status_columns=["Status"],
                    target_columns=["Receipt / Queue"],
                ),
                use_container_width=True,
                hide_index=True,
            )

    with tab_receipts:
        st.subheader("Reconciliation by receipt")
        st.caption("Each row shows one receipt target: a linked payment batch, a chargeback, a rejected transaction, or an unlinked balance.")
        st.dataframe(
            format_display_frame(
                prepare_receipt_grid(receipt_summary, receipt_payment_batch_summary),
                channel_columns=["Channel"],
                outcome_columns=["Overall Outcome"],
                status_columns=["Line Status"],
                target_columns=["Payment Batch / Queue"],
            ),
            use_container_width=True,
            hide_index=True,
        )

        receipt_options = receipt_summary["receipt_ref"].tolist()
        if receipt_options:
            default_receipt_index = receipt_options.index(query_receipt) if query_receipt in receipt_options else 0
            selected_receipt = st.selectbox("Select receipt", receipt_options, index=default_receipt_index)
            receipt_row = receipt_summary[receipt_summary["receipt_ref"] == selected_receipt].iloc[0]
            receipt_breakdown_raw = receipt_payment_batch_summary[
                receipt_payment_batch_summary["receipt_ref"] == selected_receipt
            ].copy()
            receipt_breakdown = prepare_receipt_breakdown(receipt_breakdown_raw)
            receipt_detail = receipt_lines[receipt_lines["receipt_ref"] == selected_receipt].copy()

            r1, r2, r3, r4 = st.columns(4)
            with r1:
                render_metric("Receipt", selected_receipt, "Single-channel receipt with multiple transaction lines.")
            with r2:
                render_metric("Receipt Total", money(receipt_row["receipt_total"]), "Sum of all receipt lines.")
            with r3:
                render_metric(
                    "Linked Batch Total",
                    money(receipt_row["linked_payment_batch_total"]),
                    "Amount tied back to payment batches.",
                )
            with r4:
                render_metric(
                    "Outcome",
                    prettify_outcome(receipt_row["reconciliation_outcome"]),
                    "Receipt-level reconciliation outcome.",
                )

            st.caption(describe_distribution(selected_receipt, float(receipt_row["receipt_total"]), receipt_breakdown))

            st.markdown("**Payment batch / queue breakdown**")
            st.dataframe(
                format_display_frame(
                    receipt_breakdown,
                    status_columns=["Line Status"],
                    target_columns=["Payment Batch / Queue"],
                ),
                use_container_width=True,
                hide_index=True,
            )

            st.markdown("**Line detail**")
            st.dataframe(
                format_display_frame(
                    prepare_receipt_lines(receipt_detail),
                    status_columns=["Linked Status", "Receipt Exception"],
                    target_columns=["Payment Batch / Queue"],
                ),
                use_container_width=True,
                hide_index=True,
            )

    with tab_source:
        st.subheader("Source evidence")
        st.caption("Sanitized raw inputs loaded before the SQL parsing, keying, matching, and reporting layers run.")

        src1, src2, src3 = st.columns(3)
        with src1:
            render_metric("Raw Payment-Batch Lines", str(len(raw_payment_batches)), "Internal-side financial records.")
        with src2:
            render_metric("Raw Receipt Lines", str(len(raw_receipts)), "Provider or bank-side evidence.")
        with src3:
            render_metric("Gateway Mappings", str(len(raw_gateway_reference_mapping)), "Reference bridge for e-commerce tokens.")

        st.markdown("**Raw payment batches**")
        st.dataframe(
            format_display_frame(
                prepare_source_payment_batches(raw_payment_batches),
                channel_columns=["Channel"],
            ),
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("**Raw receipts**")
        st.dataframe(
            format_display_frame(
                prepare_source_receipts(raw_receipts),
                channel_columns=["Channel"],
                status_columns=["Provider Status"],
            ),
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("**Gateway reference mapping**")
        st.dataframe(
            format_display_frame(
                prepare_source_mapping(raw_gateway_reference_mapping),
                channel_columns=["Source Channel"],
            ),
            use_container_width=True,
            hide_index=True,
        )

    with tab_runtime:
        st.subheader("Runtime and SQL")
        st.caption("The app stays focused on the live reconciliation flow. Broader scenario modeling stays in the portfolio documentation.")

        left, right = st.columns([1.15, 1])
        with left:
            st.markdown(
                """
                **Runtime layers**

                1. `sample_data/payment_batches_sample.csv`
                   compact ERP-like payment-batch lines.
                2. `sample_data/receipts_sample.csv`
                   compact receipt lines split cleanly by channel.
                3. `sample_data/gateway_reference_mapping_sample.csv`
                   token-to-reservation evidence for e-commerce.
                4. `sql/01_raw_to_parsed.sql` and `sql/02_key_generation.sql`
                   parsing and key creation.
                5. `sql/03_reconciliation_logic.sql`, `sql/04_reporting_views.sql`, `sql/05_bi_views.sql`
                   matching engine plus reporting layer.
                """
            )
            st.markdown(
                """
                **Current sample design**

                - Most payment-batch lines reconcile directly to receipt evidence.
                - A small number of lines remain in review queues.
                - Some receipts contain chargeback examples.
                - One receipt contains rejected provider-side evidence.
                - E-commerce receipts use gateway-token mapping before matching.
                """
            )
        with right:
            perf_df = pd.DataFrame(
                [
                    {"Metric": "Engine build (DuckDB + SQL)", "Seconds": float(engine["build_seconds"])},
                    {"Metric": "Snapshot load", "Seconds": float(runtime["query_seconds"])},
                    {
                        "Metric": "Total first-load runtime",
                        "Seconds": float(engine["build_seconds"]) + float(runtime["query_seconds"]),
                    },
                ]
            )
            st.markdown("**Runtime object counts**")
            st.dataframe(runtime_summary, use_container_width=True, hide_index=True)
            st.markdown("**Performance profile**")
            st.dataframe(perf_df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
