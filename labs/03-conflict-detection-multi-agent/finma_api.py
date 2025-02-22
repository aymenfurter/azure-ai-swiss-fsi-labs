from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import requests

@dataclass
class SearchResult:
    RegistrationNumber: str
    Name: str
    LegalSeat: str
    Id: str
    Link: str
    Title: Optional[str] = None
    Category: Optional[str] = None
    Timestamp: int = 0
    Tab: str = "tab1"
    Panel: str = "panel1"

@dataclass
class FacetValue:
    id: str
    Name: str
    category: str
    AggregateCount: int
    selected: bool = False

@dataclass
class Facet:
    Name: str
    Values: List[FacetValue]

@dataclass
class BankruptcyInfo:
    Finishedcount: int = 0
    Pendingcount: int = 0

@dataclass
class SearchResponse:
    Items: List[SearchResult]
    Count: int
    Searchstring: str
    Facets: List[Facet]
    NextPageLink: Optional[str]
    LastPageLink: Optional[str]
    ResultsPerPage: int
    Skip: int
    MaxResultCount: int
    Bankruptcy: BankruptcyInfo

class FinmaClient:
    BASE_URL = "https://www.finma.ch"
    SEARCH_DS = "{33E1F240-35A3-46B2-ADC3-61F936C7E186}"
    
    def search(self, query: str, order: int = 4, skip: int = 0) -> SearchResponse:
        """
        Search for entities in FINMA registry
        
        Args:
            query: Search term
            order: Sort order (default=4)
            skip: Number of results to skip for pagination
            
        Returns:
            SearchResponse containing results and facets
        """
        url = f"{self.BASE_URL}/en/api/search/getresult"
        
        data = {
            "ds": self.SEARCH_DS,
            "query": query,
            "Order": order
        }
        
        if skip > 0:
            data["Skip"] = skip
            
        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
            data = response.json()
            
            # Convert items to SearchResult objects
            items = [SearchResult(**item) for item in data["Items"]]
            
            # Convert facets
            facets = []
            for facet in data["Facets"]:
                values = [FacetValue(**v) for v in facet["Values"]]
                facets.append(Facet(Name=facet["Name"], Values=values))
                
            # Create bankruptcy info
            bankruptcy = BankruptcyInfo(**data["Bankruptcy"])
            
            return SearchResponse(
                Items=items,
                Count=data["Count"],
                Searchstring=data["Searchstring"],
                Facets=facets,
                NextPageLink=data.get("NextPageLink"),
                LastPageLink=data.get("LastPageLink"),
                ResultsPerPage=data["ResultsPerPage"],
                Skip=data["Skip"],
                MaxResultCount=data["MaxResultCount"],
                Bankruptcy=bankruptcy
            )
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to search FINMA registry: {str(e)}")