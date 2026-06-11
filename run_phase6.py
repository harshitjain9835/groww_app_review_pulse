import json
import logging
import asyncio

from doc_section import build_doc_blocks
from email_teaser import build_email_teaser
from mcp_client import PulseMCPClient

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def test_renderers():
    logger.info("--- Testing Output Renderers ---")
    
    # Mock report data simulating the output from summarizer.py (Phase 3)
    mock_report = [
        {
            "theme_name": "App Performance & Bugs",
            "summary": "Users are experiencing frequent crashes and lag during market hours.",
            "quotes": ["The app freezes exactly when the market opens, very frustrating."],
            "action_ideas": [
                {"title": "Stabilize peak-time performance", "detail": "Scale infra during market hours; improve crash visibility."}
            ]
        },
        {
            "theme_name": "Customer Support",
            "summary": "Long wait times and unhelpful bot responses.",
            "quotes": ["Support takes days to reply and doesn't solve the issue."],
            "action_ideas": [
                {"title": "Improve support SLA visibility", "detail": "Expected response time in-app; ticket status tracking."}
            ]
        }
    ]

    # 1. Test doc_section.py
    doc_text = build_doc_blocks(
        report_data=mock_report,
        product_name="Groww",
        iso_week="2026-W23",
        window_weeks=10
    )
    logger.info("\nGenerated Doc Text (Payload for Docs MCP):")
    print(doc_text)

    with open("g:\\project 3\\doc_section.json", "w", encoding="utf-8") as f:
        json.dump({"text": doc_text}, f, indent=2)
    logger.info("Saved doc payload to doc_section.json")

    # 2. Test email_teaser.py
    subject, html_body, text_body = build_email_teaser(
        report_data=mock_report,
        product_name="Groww",
        iso_week="2026-W23",
        doc_url="https://docs.google.com/document/d/12345/edit#heading=h.abc123xyz"
    )
    logger.info(f"\nGenerated Email Subject: {subject}")
    logger.info("\nGenerated Email Text Body:")
    print(text_body)

    email_payload = {
        "subject": subject,
        "html_body": html_body,
        "text_body": text_body
    }
    with open("g:\\project 3\\email_section.json", "w", encoding="utf-8") as f:
        json.dump(email_payload, f, indent=2)
    logger.info("Saved email payload to email_section.json")

async def test_mcp_client():
    logger.info("\n--- Testing MCP Client Initialization ---")
    client = PulseMCPClient()
    logger.info("MCP Client instantiated successfully.")
    logger.info("Note: Node.js MCP servers (Phase 4 & 5) need to be built before full connections can be established.")
    await client.close()

if __name__ == "__main__":
    asyncio.run(test_renderers())
    asyncio.run(test_mcp_client())
