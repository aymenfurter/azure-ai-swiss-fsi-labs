from dataclasses import dataclass
from typing import List, Optional
import requests

@dataclass
class CompanySearchResult:
    name: str
    ehraid: int
    uid: str
    uidFormatted: Optional[str]
    chid: Optional[str]
    chidFormatted: Optional[str]
    legalSeatId: int
    legalSeat: str
    registerOfficeId: int
    legalFormId: int
    status: str
    rabId: int
    shabDate: str
    deleteDate: Optional[str]
    cantonalExcerptWeb: Optional[str]

@dataclass
class SearchResponse:
    list: List[CompanySearchResult]
    offset: int
    maxEntries: int
    hasMoreResults: bool
    maxOffset: int

class ZefixClient:
    BASE_URL = "https://www.zefix.admin.ch/ZefixREST/api/v1"
    
    def search(self, 
              name: str, 
              language: str = "en",
              max_entries: int = 30,
              offset: int = 0,
              include_deleted: bool = True) -> SearchResponse:
        """
        Search for companies in the Zefix registry
        
        Args:
            name: Company name to search for
            language: Language for results (en, de, fr, it)
            max_entries: Maximum number of results per page
            offset: Pagination offset
            include_deleted: Whether to include deleted companies
            
        Returns:
            SearchResponse object containing results
        """
        url = f"{self.BASE_URL}/firm/search.json"
        
        payload = {
            "languageKey": language,
            "maxEntries": max_entries,
            "offset": offset,
            "name": name,
            "deletedFirms": include_deleted
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Convert raw response to SearchResponse model
            companies = [CompanySearchResult(**c) for c in data["list"]]
            return SearchResponse(
                list=companies,
                offset=data["offset"],
                maxEntries=data["maxEntries"], 
                hasMoreResults=data["hasMoreResults"],
                maxOffset=data["maxOffset"]
            )
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to search Zefix API: {str(e)}")