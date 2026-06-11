import re

class PIIScrubber:
    def __init__(self):
        # Standard email pattern
        self.email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        # Indian phone numbers (+91, 091, or 10 digits starting with 6-9)
        self.phone_pattern = re.compile(r'(?:(?:\+|0{0,2})91[\s-]?)?[6789]\d{9}')
        # Long numeric sequences (e.g., Aadhaar, PAN-like, Credit Cards) - 10+ digits
        self.long_num_pattern = re.compile(r'\b\d{10,}\b')

    def scrub(self, text: str) -> str:
        """
        Redacts PII from the given text string.
        """
        if not text:
            return text
            
        text = self.email_pattern.sub('[EMAIL]', text)
        text = self.phone_pattern.sub('[PHONE]', text)
        text = self.long_num_pattern.sub('[ID]', text)
        
        return text