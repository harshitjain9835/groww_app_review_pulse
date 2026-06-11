import os
import json
import asyncio
import logging
from mcp_client import PulseMCPClient

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

async def verify_gmail_mcp():
    client = PulseMCPClient()
    server_name = "fastapi-server"

    try:
        logger.info("--- Phase 5: Gmail API Integration Verification ---")
        logger.info(f"Connecting to REST API at {client.base_url}...")

        def extract_text(res):
            if hasattr(res, 'content'):
                return "\n".join([getattr(c, 'text', str(c)) for c in res.content])
            if isinstance(res, dict):
                return json.dumps(res, indent=2)
            return str(res)

        # 0. Discover available endpoints to prevent 404 Not Found errors
        available_tools = []
        try:
            api_res = await client.client.get(f"{client.base_url}/openapi.json")
            if api_res.status_code == 200:
                available_tools = [p.strip("/") for p in api_res.json().get("paths", {}).keys() if p != "/"]
                logger.info(f"Discovered server endpoints: {available_tools}")
        except Exception as e:
            logger.warning(f"Could not fetch server schema: {e}")

        def get_endpoint(candidates):
            if not available_tools:
                return candidates[0] # Fallback if discovery failed
            for c in candidates:
                if c in available_tools:
                    return c
            return None

        test_email = os.getenv("TEST_EMAIL_RECIPIENT", "").strip()
        
        if test_email:
            logger.info(f"\nFound TEST_EMAIL_RECIPIENT. Testing live tools for Email: {test_email}")
            
            # Default payload if JSON isn't found
            subject = "Groww Weekly Review Pulse - Test"
            html_body = "<h1>Test Email</h1><p>This is a test from Phase 5 verification.</p>"
            text_body = "Test Email\nThis is a test from Phase 5 verification."
            
            email_json_path = "g:\\project 3\\email_section.json"
            if os.path.exists(email_json_path):
                with open(email_json_path, "r", encoding="utf-8") as f:
                    email_payload = json.load(f)
                    subject = email_payload.get("subject", subject)
                    html_body = email_payload.get("html_body", html_body)
                    text_body = email_payload.get("text_body", text_body)
            
            # 1. Test Idempotency Check
            idempotency_key = "groww-test-phase5-email"
            idem_tool = get_endpoint(["check_idempotency", "idempotency"])
            if idem_tool:
                try:
                    logger.info(f"\nCalling '{idem_tool}' with key: {idempotency_key}")
                    idem_res = await client.call_tool(server_name, idem_tool, {"idempotency_key": idempotency_key})
                    logger.info(f"Idempotency Result:\n{extract_text(idem_res)}")
                except Exception as e:
                    logger.warning(f"{idem_tool} failed or not implemented yet: {e}")
                    if hasattr(e, 'response') and hasattr(e.response, 'text'):
                        logger.warning(f"Server response details: {e.response.text}")
            else:
                logger.warning("\nSkipping Idempotency Check (Endpoint not found on remote server).")

            # 2. Test Create Draft
            test_args = {
                "to": [e.strip() for e in test_email.split(",") if e.strip()],
                "subject": subject,
                "html_body": html_body,
                "text_body": text_body,
                "idempotency_key": idempotency_key
            }
            
            draft_tool = get_endpoint(["create_email_draft", "create_draft", "gmail_create_draft"])
            if draft_tool:
                try:
                    logger.info(f"\nCalling '{draft_tool}' with args: {test_args}")
                    res = await client.call_tool(server_name, draft_tool, test_args)
                    logger.info(f"Draft Result:\n{extract_text(res)}")
                except Exception as e:
                    logger.error(f"Create draft failed. Error: {e}")
                    if hasattr(e, 'response') and hasattr(e.response, 'text'):
                        logger.error(f"Validation Details: {e.response.text}")
            else:
                logger.warning("\nSkipping Create Draft (Endpoint not found on remote server).")
                
            # 3. Test Send Email
            send_tool = get_endpoint(["send_email", "send_mail", "send_email_draft", "gmail_send"])
            if send_tool:
                try:
                    logger.info(f"\nCalling '{send_tool}' with args: {test_args}")
                    res = await client.call_tool(server_name, send_tool, test_args)
                    logger.info(f"Send Email Result:\n{extract_text(res)}")
                except Exception as e:
                    logger.error(f"Send email failed. Error: {e}")
                    if hasattr(e, 'response') and hasattr(e.response, 'text'):
                        logger.error(f"Validation Details: {e.response.text}")
            else:
                logger.warning("\nSkipping Send Email (Endpoint not found on remote server).")
            
        else:
            logger.info("\nSkipping live execution. To run, set the 'TEST_EMAIL_RECIPIENT' environment variable in your .env file (copy from .env.example).")

    except Exception as e:
        logger.error(f"Error during Phase 5 verification: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(verify_gmail_mcp())
