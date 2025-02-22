from dataclasses import dataclass
from typing import List, Optional, Set
import pandas as pd
import requests
from datetime import datetime, timedelta
import os
from pathlib import Path
from thefuzz import fuzz

@dataclass
class SanctionedEntity:
    ssid: str
    program: str
    sanctions: str
    type: str
    name: str

class SecoClient:
    EXCEL_URL = "https://www.sesam.search.admin.ch/sesam-search-web/pages/search.xhtml"
    CACHE_DIR = Path.home() / ".cache" / "seco"
    CACHE_DURATION = timedelta(hours=24)
    
    def __init__(self):
        """Initialize SECO client with cache directory"""
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._sanctions_list: Optional[List[str]] = None

    def _download_excel(self) -> Path:
        """Download sanctions Excel file"""
        params = {
            "Applikations-Version": "1.4.0-92",
            "lang": "en",
            "nameNamensteile": "",
            "volltextsuche": "",
            "sanktionsprogrammId": "",
            "adressatTyp": "",
            "action": "generateExcelAction"
        }
        
        cache_file = self.CACHE_DIR / "sanctions.xlsx"
        
        # Check if cached file exists and is recent
        if cache_file.exists():
            mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
            if datetime.now() - mtime < self.CACHE_DURATION:
                return cache_file
        
        # Download new file
        response = requests.get(self.EXCEL_URL, params=params)
        response.raise_for_status()
        
        with open(cache_file, "wb") as f:
            f.write(response.content)
            
        return cache_file

    def _load_sanctions(self) -> List[str]:
        """Load and parse sanctions Excel file"""
        if self._sanctions_list is None:
            excel_file = self._download_excel()
            df = pd.read_excel(excel_file)
            # Get unique names from column 5 (index 4)
            self._sanctions_list = df.iloc[:, 4].unique().tolist()
        return self._sanctions_list

    def get_random_sanctioned_person(self) -> str:
        """Get a random person from the sanctions list"""
        import random
        sanctions = self._load_sanctions()
        return random.choice(sanctions)

    def _normalize_name(self, name: str) -> str:
        """Normalize name for comparison"""
        return name.lower().strip().replace(',', ' ').replace('.', ' ')

    def _get_name_variations(self, name: str) -> Set[str]:
        """Generate variations of a name for matching"""
        name = self._normalize_name(name)
        parts = [p for p in name.split() if len(p) > 1]  # Skip initials
        variations = set()
        
        # Original order
        variations.add(' '.join(parts))
        
        # Reverse order (last name first)
        if len(parts) > 1:
            variations.add(' '.join(parts[::-1]))
        
        # First + last name only
        if len(parts) > 2:
            variations.add(f"{parts[0]} {parts[-1]}")
            variations.add(f"{parts[-1]} {parts[0]}")
        
        return variations

    def search(self, name: str, threshold: int = 85) -> List[str]:
        """
        Search for a name in the sanctions list with fuzzy matching
        
        Args:
            name: Name to search for
            threshold: Fuzzy matching threshold (0-100)
            
        Returns:
            List of matching sanctioned entity names
        """
        variations = self._get_name_variations(name)
        sanctions = self._load_sanctions()
        matches = set()

        for sanctioned in sanctions:
            normalized = self._normalize_name(sanctioned)
            
            # Direct matching of name variations
            sanctioned_variations = self._get_name_variations(sanctioned)
            if any(v in sanctioned_variations for v in variations):
                matches.add(sanctioned)
                continue
                
            # Fuzzy matching as fallback
            for variant in variations:
                if fuzz.ratio(variant, normalized) >= threshold:
                    matches.add(sanctioned)
                    break
                    
                # Try partial matching for longer names
                if len(normalized.split()) > 2:
                    if fuzz.partial_ratio(variant, normalized) >= threshold:
                        matches.add(sanctioned)
                        break

        return sorted(list(matches))
    
    def is_sanctioned(self, name: str) -> bool:
        """
        Check if a name appears in the sanctions list
        
        Args:
            name: Name to check
            
        Returns:
            True if name is found in sanctions list, False otherwise
        """
        return len(self.search(name)) > 0