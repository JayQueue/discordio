"""Text parsing utilities for extracting structured data from responses."""
import re
from typing import List, Dict

class RecommendationParser:
    """Parser for movie and TV show recommendations."""
    
    @staticmethod
    def parse_recommendations(text: str) -> List[Dict[str, str]]:
        """Parse formatted recommendations into structured data."""
        recommendations = []
        # Pattern handles: "1. Title (Year) - Description" or "1. Title (Year-Year) - Description"
        pattern = r'^\d+\.\s*(.+?)\s*\((\d{4}(?:-\d{4}|-)?)\)\s*-\s*(.+)$'
        
        for line in text.split('\n'):
            line = line.strip()
            match = re.match(pattern, line)
            if match:
                recommendations.append({
                    'title': match.group(1).strip(),
                    'year': match.group(2).strip(),
                    'description': match.group(3).strip()
                })
        
        return recommendations
