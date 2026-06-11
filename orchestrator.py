import os
import json
import logging
import asyncio
import uuid
from datetime import datetime, timezone

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from mcp_client import PulseMCPClient
from store import RunLedger
from models import RunRecord, DeliveryRecord

logger = logging.getLogger(__name__)

class PulseOrchestrator:
    def __init__(self, ledger_db_path="data/ledger.db"):
        self.ledger = RunLedger(ledger_db_path)

    async def run_pipeline(self, product: str, iso_week: str, test_doc_id: str, test_email: str):
        # 1. Idempotency Check in SQLite Ledger
        existing_run = self.ledger.get_successful_run(product, iso_week)
        if existing_run:
            logger.info(f"✅ Run for '{product}' '{iso_week}' already completed successfully. Skipping pipeline.")
            return existing_run

        run_id = str(uuid.uuid4())
        started_at = datetime.now(timezone.utc).isoformat()
        logger.info(f"🚀 Starting orchestration run {run_id} for {product} {iso_week}")

        # Mocking Phases 1-3
        logger.info("Mocking Phase 1-3: Scrape, PII Scrub, Embed, Cluster, LLM Summarization...")
        review_count = 872 
        
        # Output Generation
        logger.info("Mocking Phase 6: Output renderers (Loading from local JSONs)...")
        doc_text = "Generated Report Section...\n"
        doc_json = "doc_section.json"
        if os.path.exists(doc_json):
            with open(doc_json, "r", encoding="utf-8") as f:
                doc_text = json.load(f).get("text", doc_text)
                
        email_subject, email_html, email_text = f"{product} Pulse", "", ""
        email_json = "email_section.json"
        if os.path.exists(email_json):
            with open(email_json, "r", encoding="utf-8") as f:
                em = json.load(f)
                email_subject = em.get("subject", email_subject)
                email_html = em.get("html_body", email_html)
                email_text = em.get("text_body", email_text)

        deliveries = []
        status = "failed"
        error_message = None

        mcp_client = PulseMCPClient()
        try:
            logger.info("Connecting to MCP Client...")
            api_res = await mcp_client.client.get(f"{mcp_client.base_url}/openapi.json")
            available_tools = []
            if api_res.status_code == 200:
                available_tools = [p.strip("/") for p in api_res.json().get("paths", {}).keys() if p != "/"]
                
            def get_endpoint(candidates):
                if not available_tools:
                    return candidates[0] if candidates else None
                for c in candidates:
                    if c in available_tools: return c
                return None

            is_dry_run = os.getenv("DRY_RUN", "false").lower() == "true"
            
            if is_dry_run:
                logger.info("🛑 DRY RUN ENABLED: Skipping MCP tool executions.")
                status = "completed (dry-run)"
            else:
                if test_doc_id:
                    logger.info(f"Appending section to Doc: {test_doc_id}")
                    await mcp_client.call_tool("fastapi-server", "append_to_doc", {"doc_id": test_doc_id, "content": doc_text})
                    deliveries.append(DeliveryRecord(channel="google_doc", external_id=test_doc_id))
                
                if test_email:
                    logger.info(f"Sending email to: {test_email}")
                    send_tool = get_endpoint(["send_email", "send_mail", "gmail_send", "send_email_draft", "create_email_draft", "create_draft"])
                    email_args = {"to": test_email, "subject": email_subject, "html_body": email_html, "text_body": email_text, "idempotency_key": f"{product}-{iso_week}-email"}
                    if send_tool:
                        await mcp_client.call_tool("fastapi-server", send_tool, email_args)
                        deliveries.append(DeliveryRecord(channel="gmail", external_id="sent", idempotency_key=email_args["idempotency_key"]))
                    else:
                        logger.warning(f"No suitable email endpoint found among available tools: {available_tools}. Skipping email delivery.")
                    
                status = "completed"
                logger.info("🎉 Pipeline MCP execution successful!")
        except Exception as e:
            logger.error(f"❌ Pipeline failed during MCP execution: {e}")
            error_message = str(e)
        finally:
            await mcp_client.close()

        run_record = RunRecord(run_id=run_id, product=product, iso_week=iso_week, status=status, review_count=review_count, window_weeks=10, started_at=started_at, completed_at=datetime.now(timezone.utc).isoformat(), error_message=error_message, deliveries=deliveries)
        self.ledger.record_run(run_record)
        return run_record
