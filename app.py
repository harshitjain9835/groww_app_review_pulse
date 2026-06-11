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

st.set_page_config(page_title="Groww Review Pulse", page_icon="📈", layout="wide")

# Custom UI styling based on a modern, Groww-like design
st.markdown("""
    <style>
    .main {
        background-color: #f7f9fc;
    }
    .stButton>button {
        background-color: #00d09c;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        font-weight: 600;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #00b386;
        color: white;
        box-shadow: 0 4px 8px rgba(0,208,156,0.3);
    }
    h1, h2, h3 {
        color: #1a1a1a;
        font-weight: 700;
    }
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        text-align: center;
        margin-bottom: 20px;
    }
    .metric-value {
        font-size: 2em;
        font-weight: 800;
        color: #00d09c;
    }
    .metric-label {
        color: #666;
        font-size: 0.9em;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    </style>
""", unsafe_allow_html=True)

# Header
col1, col2 = st.columns([1, 4])
with col1:
    st.image("https://groww.in/logo-groww270.png", width=150) # Groww Logo
with col2:
    st.title("App Review Pulse Dashboard")
    st.markdown("Automated insights from Google Play reviews via MCP pipeline.")

st.sidebar.title("🎛️ Control Panel")
product = st.sidebar.selectbox("Target Product", ["groww", "groww-mutual-funds"])

current_week = datetime.now().strftime("%G-W%V")
iso_week = st.sidebar.text_input("Target ISO Week", value=current_week)

st.sidebar.markdown("---")
st.sidebar.info("💡 **Tip**: Run the pipeline every Monday to gather the previous week's insights.")

tab1, tab2, tab3 = st.tabs(["🚀 Execution", "📊 Ledger History", "👀 Artifact Preview"])

with tab1:
    st.markdown("### Trigger Pipeline Run")
    st.write(f"Manually trigger the automated pipeline for **{product.capitalize()}** (Week: **{iso_week}**).")
    
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Target Product</div><div class="metric-value">{product.capitalize()}</div></div>', unsafe_allow_html=True)
    with col_b:
        st.markdown(f'<div class="metric-card"><div class="metric-label">ISO Week</div><div class="metric-value">{iso_week}</div></div>', unsafe_allow_html=True)
    with col_c:
        db_path = "data/ledger.db"
        run_count = 0
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM runs WHERE status='completed'")
            run_count = cur.fetchone()[0]
            conn.close()
        st.markdown(f'<div class="metric-card"><div class="metric-label">Total Successful Runs</div><div class="metric-value">{run_count}</div></div>', unsafe_allow_html=True)
    
    if st.button("🚀 Execute Pulse Pipeline"):
        with st.spinner("🔄 Executing Pipeline... Scrape -> Scrub -> Embed -> Cluster -> LLM -> MCP Delivery"):
            doc_id = os.getenv("TEST_DOC_ID")
            email = os.getenv("TEST_EMAIL_RECIPIENT")
            
            if not doc_id or not email:
                st.error("⚠️ Missing TEST_DOC_ID or TEST_EMAIL_RECIPIENT configuration in .env file.")
            else:
                orchestrator = PulseOrchestrator()
                try:
                    record = asyncio.run(orchestrator.run_pipeline(product, iso_week, doc_id, email))
                    if "completed" in record.status:
                        st.success(f"✅ Run Execution Finished! Status: {record.status}")
                        st.balloons()
                    else:
                        st.error(f"❌ Run Execution Finished! Status: {record.status}")
                    
                    with st.expander("View Run Record Details"):
                        st.json(record.model_dump())
                except Exception as e:
                    st.error(f"🚨 Pipeline Execution Failed: {e}")

with tab2:
    st.markdown("### Run Ledger Database")
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        
        st.subheader("Recent Runs")
        df_runs = pd.read_sql_query(f"SELECT run_id, product, iso_week, status, review_count, started_at FROM runs WHERE product='{product}' ORDER BY started_at DESC", conn)
        
        def color_status(val):
            color = '#00d09c' if 'completed' in val else '#ff4b4b' if 'failed' in val else '#ffa500'
            return f'color: {color}; font-weight: bold;'
            
        st.dataframe(df_runs.style.map(color_status, subset=['status']), use_container_width=True, hide_index=True)
        
        st.subheader("MCP Delivery Receipts")
        df_del = pd.read_sql_query("SELECT id, run_id, channel, external_id, idempotency_key FROM deliveries ORDER BY id DESC LIMIT 50", conn)
        st.dataframe(df_del, use_container_width=True, hide_index=True)
        conn.close()
    else:
        st.info("ℹ️ Ledger Database does not exist yet. Try running the pipeline first!")
        
with tab3:
    st.markdown("### Artifacts Snapshot")
    st.write("Preview the outputs generated during the local mock or dry-run execution.")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📄 Google Doc Appended Content")
        if os.path.exists("doc_section.json"):
            try:
                doc_data = json.load(open("doc_section.json", "r", encoding="utf-8"))
                st.text_area("Plain Text Generated (Sent to Docs MCP):", doc_data.get("text", ""), height=400)
            except Exception:
                st.warning("Could not load doc_section.json")
        else:
            st.info("No doc_section.json found.")
            
    with col2:
        st.markdown("#### 📧 Generated Email Teaser")
        if os.path.exists("email_section.json"):
            try:
                em_data = json.load(open("email_section.json", "r", encoding="utf-8"))
                st.text_input("Subject Line:", em_data.get("subject", ""))
                st.markdown("**HTML Body Preview:**")
                st.components.v1.html(em_data.get("html_body", ""), height=330, scrolling=True)
            except Exception:
                st.warning("Could not load email_section.json")
        else:
            st.info("No email_section.json found.")
