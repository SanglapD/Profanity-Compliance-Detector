
import streamlit as st
import pandas as pd
import os

PATTERN_CSV_PATH = "./outputs/regex_summary.csv"
ML_CSV_PATH = "./outputs/gemini_summary.csv"

def _as_bool_series(series: pd.Series, length: int) -> pd.Series:
    if series is None:
        return pd.Series([False] * length)
    if series.dtype == bool:
        return series.fillna(False)
    return series.astype(str).str.strip().str.lower().map(
        {"true": True, "1": True, "yes": True, "y": True,
         "false": False, "0": False, "no": False, "n": False}
    ).fillna(False)

def load_csv_from_path(path: str) -> pd.DataFrame:
    if not path or not os.path.exists(path):
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception as e:
        st.error(f"Failed to read CSV at {path}: {e}")
        return pd.DataFrame()

def show_pattern_profanity(df: pd.DataFrame) -> None:
    if df.empty:
        st.info(f"Pattern Matching CSV not found or empty at: {PATTERN_CSV_PATH}")
        return
    n = len(df)
    for col in ["profanity_agent", "profanity_customer"]:
        if col in df.columns:
            df[col] = _as_bool_series(df[col], n)

    st.subheader("Q1 · Profanity Detection (Pattern Matching)")
    agents = df.loc[df.get("profanity_agent", pd.Series([False]*n)) == True, "call_id"].unique()
    customers = df.loc[df.get("profanity_customer", pd.Series([False]*n)) == True, "call_id"].unique()

    if len(agents) == 0 and len(customers) == 0:
        st.success("No profanity detected by agents or customers.")
        return

    if len(agents):
        st.markdown("**Call IDs where agents used profanity:**")
        st.table(pd.DataFrame({"call_id": agents}))
    else:
        st.info("No agents used profanity.")

    if len(customers):
        st.markdown("**Call IDs where customers used profanity:**")
        st.table(pd.DataFrame({"call_id": customers}))
    else:
        st.info("No customers used profanity.")

def show_pattern_privacy(df: pd.DataFrame) -> None:
    if df.empty:
        st.info(f"Pattern Matching CSV not found or empty at: {PATTERN_CSV_PATH}")
        return
    n = len(df)
    col = "info_shared_without_identity_verification"
    if col in df.columns:
        df[col] = _as_bool_series(df[col], n)

    st.subheader("Q2 · Privacy & Compliance (Pattern Matching)")
    viol = df.loc[df.get(col, pd.Series([False]*n)) == True, "call_id"].unique()
    if len(viol) == 0:
        st.success("No cases where sensitive info was shared before verification.")
    else:
        st.markdown("**Call IDs with info shared before verification (violation):**")
        st.table(pd.DataFrame({"call_id": viol}))

def show_ml_profanity(df: pd.DataFrame) -> None:
    if df.empty:
        st.info(f"ML/LLM CSV not found or empty at: {ML_CSV_PATH}")
        return

    n = len(df)
    if "profane_words_agent" in df.columns:
        df["profane_words_agent"] = _as_bool_series(df["profane_words_agent"], n)
        agent_flags = df["profane_words_agent"]
    else:
        agent_flags = (df.get("agent_profane_words_count", pd.Series([0]*n)).fillna(0).astype(float) > 0)

    if "profane_words_customer" in df.columns:
        df["profane_words_customer"] = _as_bool_series(df["profane_words_customer"], n)
        customer_flags = df["profane_words_customer"]
    else:
        customer_flags = (df.get("customer_profane_words_count", pd.Series([0]*n)).fillna(0).astype(float) > 0)

    st.subheader("Q1 · Profanity Detection (ML/LLM)")
    agents = df.loc[agent_flags == True, "call_id"].astype(str).unique()
    customers = df.loc[customer_flags == True, "call_id"].astype(str).unique()

    if len(agents) == 0 and len(customers) == 0:
        st.success("No profanity detected by agents or customers.")
        return

    if len(agents):
        st.markdown("**Call IDs where agents used profanity:**")
        st.table(pd.DataFrame({"call_id": agents}))
    else:
        st.info("No agents used profanity.")

    if len(customers):
        st.markdown("**Call IDs where customers used profanity:**")
        st.table(pd.DataFrame({"call_id": customers}))
    else:
        st.info("No customers used profanity.")

def show_ml_privacy(df: pd.DataFrame) -> None:
    if df.empty:
        st.info(f"ML/LLM CSV not found or empty at: {ML_CSV_PATH}")
        return
    n = len(df)
    df["disclosed_before_verify"] = _as_bool_series(df.get("disclosed_before_verify", pd.Series([False]*n)), n)

    st.subheader("Q2 · Privacy & Compliance (ML/LLM)")
    viol = df.loc[df["disclosed_before_verify"] == True, "call_id"].astype(str).unique()
    if len(viol) == 0:
        st.success("No cases where sensitive info was shared before verification.")
    else:
        st.markdown("**Call IDs with info shared before verification (violation):**")
        st.table(pd.DataFrame({"call_id": viol}))

def main() -> None:
    st.set_page_config(page_title="Call Compliance & Quality Analysis", layout="centered")
    st.title("Call Compliance and Quality Analysis")

    pattern_df = load_csv_from_path(PATTERN_CSV_PATH)
    ml_df = load_csv_from_path(ML_CSV_PATH)

    approach = st.selectbox("Select approach", ["Pattern Matching", "ML/LLM"], index=0)
    entity = st.selectbox("Select entity", ["Profanity Detection", "Privacy & Compliance Violation"], index=0)

    if approach == "Pattern Matching" and entity == "Profanity Detection":
        show_pattern_profanity(pattern_df)
    elif approach == "Pattern Matching" and entity == "Privacy & Compliance Violation":
        show_pattern_privacy(pattern_df)
    elif approach == "ML/LLM" and entity == "Profanity Detection":
        show_ml_profanity(ml_df)
    else:
        show_ml_privacy(ml_df)

    st.divider()
    st.write("Looking for call quality metrics")
    st.page_link("./pages/02_Q3_Visualizer.py", label="Go to Call Quality Metrics")

if __name__ == "__main__":
    main()
