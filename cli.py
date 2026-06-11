import os
import sys
import asyncio
import argparse
import logging
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

# Setup paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pulse.agent.orchestrator import PulseOrchestrator

load_dotenv(dotenv_path="g:\\project 3\\.env")

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def get_current_iso_week():
    return datetime.now().strftime("%G-W%V")

async def run_pipeline(product, iso_week, dry_run=False):
    if dry_run:
        os.environ["DRY_RUN"] = "true"
        
    doc_id = os.getenv("TEST_DOC_ID")
    email = os.getenv("TEST_EMAIL_RECIPIENT")
    
    if not doc_id or not email:
        logger.error("Missing TEST_DOC_ID or TEST_EMAIL_RECIPIENT in .env file.")
        return
        
    orchestrator = PulseOrchestrator()
    await orchestrator.run_pipeline(product, iso_week, doc_id, email)

def main():
    parser = argparse.ArgumentParser(description="Weekly Product Review Pulse CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Command: run
    parser_run = subparsers.add_parser("run", help="Run the pulse pipeline for a specific week")
    parser_run.add_argument("--product", default="groww", help="Target product slug")
    parser_run.add_argument("--iso-week", default=get_current_iso_week(), help="Target ISO week (e.g. 2026-W23)")
    
    # Command: dry-run
    parser_dryrun = subparsers.add_parser("dry-run", help="Run the pipeline logic without writing to Google/MCP")
    parser_dryrun.add_argument("--product", default="groww")
    parser_dryrun.add_argument("--iso-week", default=get_current_iso_week())
    
    # Command: backfill
    parser_backfill = subparsers.add_parser("backfill", help="Backfill historical weeks")
    parser_backfill.add_argument("--product", default="groww")
    parser_backfill.add_argument("--weeks", required=True, help="Comma-separated ISO weeks (e.g. 2026-W21,2026-W22)")
    
    # Command: status
    parser_status = subparsers.add_parser("status", help="Show the ledger history")
    parser_status.add_argument("--product", default="groww")
    
    args = parser.parse_args()
    
    if args.command == "run":
        asyncio.run(run_pipeline(args.product, args.iso_week))
    elif args.command == "dry-run":
        asyncio.run(run_pipeline(args.product, args.iso_week, dry_run=True))
    elif args.command == "backfill":
        for week in [w.strip() for w in args.weeks.split(",")]:
            logger.info(f"\n--- Backfilling Week {week} ---")
            asyncio.run(run_pipeline(args.product, week))
    elif args.command == "status":
        db_path = "g:\\project 3\\data\\ledger.db"
        if os.path.exists(db_path):
            with sqlite3.connect(db_path) as conn:
                for row in conn.execute("SELECT iso_week, status, run_id, started_at FROM runs WHERE product=? ORDER BY started_at DESC LIMIT 20", (args.product,)):
                    print(f"[{row[0]}] {row[1].upper()} | Run ID: {row[2]} | Started: {row[3]}")
        else:
            print("Ledger Database does not exist yet.")

if __name__ == "__main__":
    main()