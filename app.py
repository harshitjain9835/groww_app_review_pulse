import os
import sys
import json
import sqlite3
import asyncio
import streamlit as st
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Set up absolute paths so app can find core agent logic
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from orchestrator import PulseOrchestrator

load_dotenv()

st.set_page_config(page_title="Review Pulse Dashboard", layout="wide")

st.sidebar.title("Pulse Control Panel")
product = st.sidebar.selectbox("Target Product", ["groww"])

current_week = datetime.now().strftime("%G-W%V")
iso_week = st.sidebar.text_input("Target ISO Week", value=current_week)

tab1, tab2, tab3 = st.tabs(["Trigger Run", "Run History Ledger", "Output Preview"])

with tab1:
    st.header("Trigger Pipeline Run")
    st.write(f"Manually trigger the pipeline for **{product}** (Week: **{iso_week}**).")
    
    if st.button("🚀 Execute Pulse Pipeline"):
        with st.spinner("Executing Pipeline... (Check terminal for real-time logs)"):
            doc_id = os.getenv("TEST_DOC_ID")
            email = os.getenv("TEST_EMAIL_RECIPIENT")
            
            if not doc_id or not email:
                st.error("Missing TEST_DOC_ID or TEST_EMAIL_RECIPIENT configuration in .env file.")
            else:
                orchestrator = PulseOrchestrator()
                try:
                    # Streamlit is synchronous, so we run our asyncio code like this
                    record = asyncio.run(orchestrator.run_pipeline(product, iso_week, doc_id, email))
                    st.success(f"Run Execution Finished! Status: {record.status}")
                    st.json(record.model_dump())
                except Exception as e:
                    st.error(f"Pipeline Execution Failed: {e}")

with tab2:
    st.header("Run Ledger Database")
    db_path = "data/ledger.db"
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        df_runs = pd.read_sql_query(f"SELECT run_id, product, iso_week, status, review_count, started_at FROM runs WHERE product='{product}' ORDER BY started_at DESC", conn)
        st.dataframe(df_runs, use_container_width=True)
        
        st.subheader("MCP Delivery Receipts")
        df_del = pd.read_sql_query("SELECT id, run_id, channel, external_id, idempotency_key FROM deliveries ORDER BY id DESC LIMIT 50", conn)
        st.dataframe(df_del, use_container_width=True)
        conn.close()
    else:
        st.warning("Ledger Database does not exist yet. Try running the pipeline first!")
        
with tab3:
    st.header("Artifacts Snapshot")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Google Doc Appended Content")
        if os.path.exists("doc_section.json"):
            doc_data = json.load(open("doc_section.json", "r", encoding="utf-8"))
            st.text_area("Plain Text Generated:", doc_data.get("text", ""), height=400)
            
    with col2:
        st.subheader("Generated Email HTML")
        if os.path.exists("email_section.json"):
            em_data = json.load(open("email_section.json", "r", encoding="utf-8"))
            st.text_input("Subject Line:", em_data.get("subject", ""))
            st.components.v1.html(em_data.get("html_body", ""), height=350, scrolling=True)
