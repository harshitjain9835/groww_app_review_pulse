import os
import json
import logging
from dotenv import load_dotenv

from scrubber import PIIScrubber
from embeddings import Embedder
from clustering import ReviewClustering
from summarizer import GroqSummarizer

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def main():
    # Load the GROQ_API_KEY from .env
    load_dotenv()
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        logger.error("GROQ_API_KEY not found. Please check your .env file.")
        return

    # 1. Generate 25 mock reviews (Must be >= 20 to pass clustering checks)
    mock_reviews = [
        # Cluster 1: Performance / Bugs
        {"id": "1", "text": "The app crashes every time I open it. Very bad experience.", "rating": 1},
        {"id": "2", "text": "Keeps freezing during market hours. Fix it!", "rating": 1},
        {"id": "3", "text": "App is lagging a lot since the last update.", "rating": 2},
        {"id": "4", "text": "UI is too slow to load my portfolio.", "rating": 3},
        {"id": "5", "text": "App crashes frequently on my Android device.", "rating": 1},
        {"id": "6", "text": "Slow load times. Please optimize performance.", "rating": 2},
        {"id": "7", "text": "Very buggy after the recent update.", "rating": 2},
        
        # Cluster 2: Customer Support (Contains PII to test scrubber)
        {"id": "8", "text": "Customer support is unresponsive. Sent an email to john.doe@example.com but no reply.", "rating": 1},
        {"id": "9", "text": "Support took 5 days to reply. Terrible.", "rating": 1},
        {"id": "10", "text": "No response from the helpdesk. Calling +919876543210 didn't work.", "rating": 1},
        {"id": "11", "text": "Unresponsive customer care team. My money is stuck.", "rating": 1},
        {"id": "12", "text": "Tickets get closed without any resolution. Bad support.", "rating": 1},
        {"id": "13", "text": "Chat support is a bot that doesn't understand anything.", "rating": 2},

        # Cluster 3: Positive Feedback
        {"id": "14", "text": "Great app for beginners. Very easy to use.", "rating": 5},
        {"id": "15", "text": "Smooth onboarding and intuitive design.", "rating": 5},
        {"id": "16", "text": "Best app for mutual funds investment.", "rating": 5},
        {"id": "17", "text": "The new chart features are awesome.", "rating": 4},
        {"id": "18", "text": "UI is clean and investing is just one click away.", "rating": 5},
        {"id": "19", "text": "Love the app! Highly recommended.", "rating": 5},

        # Cluster 4: Feature Requests (Dark Mode)
        {"id": "20", "text": "Where is the dark mode? Otherwise good.", "rating": 4},
        {"id": "21", "text": "Dark theme would be highly appreciated. My eyes hurt.", "rating": 4},
        {"id": "22", "text": "Please add a dark mode feature.", "rating": 3},
        {"id": "23", "text": "Needs a dark mode for night time trading.", "rating": 4},
        {"id": "24", "text": "Still waiting for dark UI.", "rating": 3},
        {"id": "25", "text": "App is too bright, dark mode is a must.", "rating": 3},
    ]

    logger.info("--- Starting Phase 2: Processing, Embeddings, Clustering ---")
    
    # PII Scrubbing
    scrubber = PIIScrubber()
    for r in mock_reviews:
        r["scrubbed_text"] = scrubber.scrub(r["text"])

    # Embeddings
    embedder = Embedder()
    embedded_reviews = embedder.generate_embeddings(mock_reviews)

    # Clustering (Setting min_cluster_size=3 since our mock data size is small)
    clustering = ReviewClustering(min_cluster_size=3)
    ranked_clusters = clustering.cluster_reviews(embedded_reviews)
    logger.info(f"Found {len(ranked_clusters)} distinct clusters.")

    logger.info("--- Starting Phase 3: LLM Summarization ---")
    summarizer = GroqSummarizer(api_key=groq_api_key)

    final_report = []
    for cluster in ranked_clusters:
        logger.info(f"Summarizing Cluster ID {cluster['cluster_id']} (Size: {cluster['size']}, Score: {cluster['score']})")
        
        # This natively checks our quote_validator internally
        summary = summarizer.summarize_cluster(cluster["cluster_id"], cluster["samples"])
        if summary:
            summary["cluster_metrics"] = {"size": cluster["size"], "score": cluster["score"]}
            final_report.append(summary)

    logger.info("\n--- Final Generated JSON Report ---")
    print(json.dumps(final_report, indent=2))

if __name__ == "__main__":
    main()