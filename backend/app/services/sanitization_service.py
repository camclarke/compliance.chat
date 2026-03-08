import json
import re
from typing import Dict, Any, List

class SanitizationService:
    """
    Handles extracting, cross-referencing, and sanitizing data from Tier 3 secondary sources.
    Ensures competitor branding is scrubbed and facts are specifically attributed to Regulation IDs.
    """

    @staticmethod
    def identify_regulation_id(text: str) -> str:
        """
        Attempts to find a structured Regulation ID (e.g. NOM-001-SCFI, FCC Part 15).
        """
        # A simple regex to catch standard formats like XXX-000-XXXX-0000
        matches = re.findall(r'[A-Z]+\-\d+\-[A-Z]+(?:\-\d{4})?', text)
        if matches:
            return matches[0]
        return "UNKNOWN_REGULATION_ID"

    @staticmethod
    def extract_technical_facts(text: str) -> Dict[str, Any]:
        """
        Extracts pure technical facts using a predefined schema. 
        In production, this would use a structured output LLM call. 
        For now, returns a dummy extracted dict.
        """
        return {
            "voltage": "220V",
            "frequency": "50Hz",
            "power_limit": "100W"
        }

    @staticmethod
    def scrub_competitor_branding(text: str) -> str:
        """
        Removes known law firm, competitor, and consultancy branding from the text.
        """
        competitors = ["Baker McKenzie", "Deloitte", "PwC", "KPMG", "EY", "SGS", "Intertek", "TÜV"]
        sanitized = text
        for competitor in competitors:
            sanitized = sanitized.replace(competitor, "[REDACTED_SECONDARY_SOURCE]")
        
        # Remove URLs
        sanitized = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '[REDACTED_URL]', sanitized)
        return sanitized

    @classmethod
    def cross_reference_and_wash(cls, source_1_text: str, source_2_text: str) -> Dict[str, Any]:
        """
        Validates that two independent secondary sources agree on technical facts.
        """
        facts_1 = cls.extract_technical_facts(source_1_text)
        facts_2 = cls.extract_technical_facts(source_2_text)

        # Cross-reference rule: if facts disagree, trigger manual review
        if facts_1 != facts_2:
            return {
                "status": "MANUAL_REVIEW_REQUIRED",
                "reason": "Secondary sources disagree on technical values.",
                "facts_source_1": facts_1,
                "facts_source_2": facts_2
            }
        
        # If they agree, wash the status and attach the Regulation ID
        reg_id = cls.identify_regulation_id(source_1_text) or cls.identify_regulation_id(source_2_text)
        
        # Return the washed proprietary data
        return {
            "status": "WASHED_PROPRIETARY",
            "attribution_id": reg_id,
            "technical_facts": facts_1
        }
