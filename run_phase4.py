import os
import json
import asyncio
import logging
from mcp_client import PulseMCPClient

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

async def verify_docs_mcp():
    client = PulseMCPClient()
    server_name = "fastapi-server"

    try:
        logger.info("--- Phase 4: Google Docs API Integration Verification ---")
        logger.info(f"Connecting to REST API at {client.base_url}...")

        test_doc_id = os.getenv("TEST_DOC_ID", "").strip()
        
        if test_doc_id:
            logger.info(f"\nFound TEST_DOC_ID. Testing live tools on Doc: {test_doc_id}")
            
            payload_text = "Test section content from Phase 4 verification script.\n"
            doc_json_path = "g:\\project 3\\doc_section.json"
            if os.path.exists(doc_json_path):
                with open(doc_json_path, "r", encoding="utf-8") as f:
                    doc_payload = json.load(f)
                    payload_text = doc_payload.get("text", payload_text)
            
            try:
                test_args = {
                    "doc_id": test_doc_id, 
                    "content": payload_text
                }
                logger.info(f"Calling 'append_to_doc' with args: {test_args}")
                res = await client.call_tool(server_name, "append_to_doc", test_args)
                logger.info(f"Result: {res}")
            except Exception as e:
                logger.error(f"Tool call failed. Error: {e}")
            
        else:
            logger.info("\nSkipping live execution. To run, set the 'TEST_DOC_ID' environment variable.")

    except Exception as e:
        logger.error(f"Error during Phase 4 verification: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(verify_docs_mcp())