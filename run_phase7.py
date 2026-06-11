import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def main():
    logger.info("--- Phase 7: Orchestration and Ledger Execution ---")
    load_dotenv(dotenv_path="g:\\project 3\\.env")

    doc_id = os.getenv("TEST_DOC_ID")
    email = os.getenv("TEST_EMAIL_RECIPIENT")

    if not doc_id or not email:
        logger.warning("Please set TEST_DOC_ID and TEST_EMAIL_RECIPIENT in your .env file to run full orchestration.")
        return

    from pulse.agent.orchestrator import PulseOrchestrator
    orchestrator = PulseOrchestrator()
    
    # Run 1: First Execution
    logger.info("\n=== First Orchestration Run ===")
    await orchestrator.run_pipeline(product="groww", iso_week="2026-W23", test_doc_id=doc_id, test_email=email)

    # Run 2: Test Idempotency
    logger.info("\n=== Second Orchestration Run (Testing Ledger Idempotency) ===")
    await orchestrator.run_pipeline(product="groww", iso_week="2026-W23", test_doc_id=doc_id, test_email=email)

if __name__ == "__main__":
    asyncio.run(main())