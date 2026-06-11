import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class QuoteValidator:
    def _normalize_text(self, text: str) -> str:
        """Standardize spaces and casing to avoid trivial validation failures."""
        if not text:
            return ""
        return re.sub(r'\s+', ' ', text.lower().strip())

    def validate_quotes(self, generated_quotes: List[str], source_reviews: List[Dict[str, Any]]) -> List[str]:
        """
        Validates that generated quotes exist as verbatim substrings in the cluster's original texts.
        Allows for '...' or '…' as valid truncations in the middle of a quote.
        """
        valid_quotes = []
        normalized_sources = [
            self._normalize_text(r.get("scrubbed_text", r.get("text", ""))) 
            for r in source_reviews
        ]
        
        for quote in generated_quotes:
            norm_quote = self._normalize_text(quote)
            
            # Split by ellipsis to handle LLM truncations
            parts = [p.strip() for p in re.split(r'\.\.\.|…', norm_quote) if p.strip()]
            if not parts:
                continue
                
            is_valid = False
            for source in normalized_sources:
                all_parts_found = True
                current_idx = 0
                
                # Sequential substring match
                for part in parts:
                    idx = source.find(part, current_idx)
                    if idx == -1:
                        all_parts_found = False
                        break
                    current_idx = idx + len(part)
                
                if all_parts_found:
                    is_valid = True
                    break
            
            if is_valid:
                valid_quotes.append(quote)
            else:
                logger.warning(f"Dropped hallucinated or unverified quote: {quote}")
                
        return valid_quotes