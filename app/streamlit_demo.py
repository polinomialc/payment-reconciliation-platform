import pandas as pd
import streamlit as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

st.set_page_config(page_title="Reconciliation Platform Demo", layout="wide")
st.title("Payment Reconciliation Platform")
st.caption("Sanitized public demo of the reconciliation project")

st.markdown(
    """
    This demo illustrates the operating model of the platform:
    - local PoC validated in DuckDB/Python
    - production target designed for BigQuery
    - Streamlit used as the guided operational interface
    """
)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Sample Receipts")
    receipts = pd.read_csv(ROOT / "sample_data" / "receipts_sample.csv")
    st.dataframe(receipts, use_container_width=True)

with col2:
    st.subheader("Sample Schedules")
    schedules = pd.read_csv(ROOT / "sample_data" / "schedules_sample.csv")
    st.dataframe(schedules, use_container_width=True)

st.subheader("Example Outputs")
out1, out2 = st.columns(2)

with out1:
    st.markdown("**Reconciliation by schedule**")
    by_schedule = pd.read_csv(ROOT / "output_examples" / "reconciliation_by_schedule.csv")
    st.dataframe(by_schedule, use_container_width=True)

with out2:
    st.markdown("**Reconciliation by receipt**")
    by_receipt = pd.read_csv(ROOT / "output_examples" / "reconciliation_by_receipt.csv")
    st.dataframe(by_receipt, use_container_width=True)

