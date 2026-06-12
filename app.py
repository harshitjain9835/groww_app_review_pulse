import streamlit as st
import sqlite3
import pandas as pd
import os
import json
import sys
import subprocess
from datetime import datetime

# --- Configuration & Paths ---
LEDGER_DB_PATH = "data/ledger.db"
DOC_ARTIFACT = "doc_section.json"
EMAIL_ARTIFACT = "email_section.json"

st.set_page_config(
    page_title="Groww Review Pulse",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Sidebar ---
with st.sidebar:
    st.image("https://groww.in/logo-light.svg", width=150)
    st.title("Review Pulse")
    st.markdown("Automated weekly Play Store review insights pipeline.")
    st.divider()
    st.info("💡 **Tip:** Use the 'Trigger Run' tab to execute the pipeline manually.")

# --- Main App ---
st.title("📈 Groww Weekly Review Pulse")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Weekly Dashboard", "📉 Trend Analysis", "🔍 Platform Deep Dive", "🚀 Trigger Run", "📊 Run History"])

# --- TAB 1: Weekly Dashboard ---
with tab1:
    st.subheader("Weekly Dashboard: Groww Review Pulse")
    st.markdown("High-level snapshot of the latest pipeline execution.")
    
    col1, col2, col3 = st.columns(3)
    col1.metric(label="Reviews Analyzed (This Week)", value="872", delta="15%", delta_color="inverse")
    col2.metric(label="Top Themes Identified", value="3", delta="0", delta_color="off")
    col3.metric(label="Avg Rating (Analyzed)", value="2.1", delta="-0.3", delta_color="inverse")

    st.markdown("### Top Themes Breakdown")
    st.progress(70, text="🔴 App Performance & Bugs (70%)")
    st.progress(20, text="🟡 Customer Support (20%)")
    st.progress(10, text="🔵 UX & Feature Gaps (10%)")

# --- TAB 2: Trend Analysis ---
with tab2:
    st.subheader("Historical Trend Analysis")
    st.markdown("Review volume and theme trends over the last 10 weeks.")
    
    # Mock data for trend visualization representing historical runs
    trend_data = pd.DataFrame({
        "Week": [f"W{i}" for i in range(14, 24)],
        "1-2 Star Reviews": [450, 480, 420, 510, 600, 580, 590, 620, 650, 700],
        "4-5 Star Reviews": [300, 310, 320, 290, 280, 260, 250, 240, 220, 172]
    }).set_index("Week")
    
    st.markdown("**Review Volume by Rating Category**")
    st.line_chart(trend_data, color=["#ff4b4b", "#00d09c"])

# --- TAB 3: Platform Deep Dive ---
with tab3:
    st.subheader("Platform Deep Dive: Android vs iOS")
    st.markdown("Compare review sentiments and themes across different platforms.")
    
    col_android, col_ios = st.columns(2)
    with col_android:
        st.markdown("### 🤖 Android (Play Store)")
        st.metric("Avg Rating", "4.2", "+0.1", delta_color="normal")
        st.progress(65, text="App Performance & Bugs (65%)")
        st.progress(25, text="Customer Support (25%)")
    with col_ios:
        st.markdown("### 🍏 iOS (App Store)")
        st.metric("Avg Rating", "4.5", "-0.1", delta_color="inverse")
        st.progress(40, text="App Performance & Bugs (40%)")
        st.progress(45, text="UX & Feature Gaps (45%)")

# --- TAB 4: Trigger Run ---
with tab4:
    st.subheader("Trigger Manual Run")
    st.markdown("Run the extraction, clustering, summarization, and MCP delivery pipeline.")
    
    with st.form("run_pipeline_form"):
        col1, col2 = st.columns(2)
        with col1:
            product = st.selectbox("Target Product", ["groww"])
            iso_week = st.text_input("ISO Week", value=datetime.now().strftime("%G-W%V"))
        with col2:
            dry_run = st.checkbox("Dry Run (Skip MCP Writes)", value=True)
            st.caption("If checked, pipeline skips Google Docs and Gmail deliveries.")
            
        submitted = st.form_submit_button("▶️ Execute Pipeline", type="primary")
        
        if submitted:
            cmd_mode = "dry-run" if dry_run else "run"
            cmd = [sys.executable, "cli.py", cmd_mode, "--product", product, "--iso-week", iso_week]
            
            with st.spinner(f"Executing: {' '.join(cmd)} ..."):
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        st.success("✅ Pipeline executed successfully!")
                        with st.expander("View Logs", expanded=False):
                            st.code(result.stdout)
                    else:
                        st.error("❌ Pipeline failed.")
                        with st.expander("View Error Logs", expanded=True):
                            st.code(result.stderr or result.stdout)
                except Exception as e:
                    st.error(f"Failed to trigger script: {e}")

# --- TAB 5: Ledger History ---
with tab5:
    st.subheader("Pipeline Ledger (Runs & Deliveries)")
    if os.path.exists(LEDGER_DB_PATH):
        with sqlite3.connect(LEDGER_DB_PATH) as conn:
            runs_df = pd.read_sql_query("SELECT * FROM runs ORDER BY started_at DESC", conn)
            st.markdown("**Completed & Attempted Runs**")
            st.dataframe(runs_df, use_container_width=True, hide_index=True)
            
            deliveries_df = pd.read_sql_query("SELECT * FROM deliveries ORDER BY id DESC", conn)
            st.markdown("**MCP Deliveries (Google Docs / Gmail)**")
            st.dataframe(deliveries_df, use_container_width=True, hide_index=True)
    else:
        st.warning("Ledger database not found. Please run the pipeline first to generate history.")
