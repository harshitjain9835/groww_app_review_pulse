import hashlib
import json
import os
import logging
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class Embedder:
    def __init__(self, cache_dir: str = "data/cache/embeddings"):
        self.model = SentenceTransformer("BAAI/bge-small-en-v1.5")
        self.cache_dir = cache_dir
        
        os.makedirs(self.cache_dir, exist_ok=True)
        self.cache_file = os.path.join(self.cache_dir, "embedding_cache.json")
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict[str, List[float]]:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load embedding cache: {e}")
        return {}

    def _save_cache(self):
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f)

    def _get_hash(self, text: str, rating: int) -> str:
        content = f"{text}_{rating}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def generate_embeddings(self, reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        texts_to_embed = []
        indices_to_embed = []

        # Pre-check cache
        for i, review in enumerate(reviews):
            text = review.get("scrubbed_text", review.get("text", ""))
            rating = review.get("rating", 0)
            cache_key = self._get_hash(text, rating)

            if cache_key in self.cache:
                review["embedding"] = self.cache[cache_key]
            else:
                texts_to_embed.append(text)
                indices_to_embed.append(i)

        # Batch request missing embeddings
        if texts_to_embed:
            chunk_size = 100
            for i in range(0, len(texts_to_embed), chunk_size):
                logger.info(f"Generating embeddings for batch {i//chunk_size + 1}...")
                chunk = texts_to_embed[i:i + chunk_size]
                chunk_indices = indices_to_embed[i:i + chunk_size]
                
                embeddings = self.model.encode(chunk).tolist()
                
                for j, emb in enumerate(embeddings):
                    orig_idx = chunk_indices[j]
                    review = reviews[orig_idx]
                    cache_key = self._get_hash(review.get("scrubbed_text", review.get("text", "")), review.get("rating", 0))
                    
                    self.cache[cache_key] = emb
                    review["embedding"] = emb
                    
            self._save_cache()

        return reviews