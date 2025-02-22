from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
import requests
from enum import Enum

class PublicationState(Enum):
    PUBLISHED = "PUBLISHED"
    CANCELLED = "CANCELLED"

@dataclass
class RegistrationOffice:
    id: str
    displayName: str
    street: str
    streetNumber: str
    swissZipCode: str
    town: str
    containsPostOfficeBox: bool
    postOfficeBox: Optional[Dict]
    municipalityId: Optional[str]
    uid: Optional[str]

@dataclass
class Municipality:
    swissZipCode: int
    town: str
    municipalityId: Optional[str]

@dataclass
class PublicationMeta:
    id: str
    creationDate: datetime
    updateDate: datetime
    rubric: str
    subRubric: str
    language: str
    registrationOffice: RegistrationOffice
    publicationNumber: str
    publicationState: str
    publicationDate: datetime
    expirationDate: Optional[datetime]
    primaryTenantCode: str
    publicationOriginator: Optional[Any] = None
    onBehalfOf: Optional[Any] = None
    invoiceAddressId: Optional[str] = None
    legalRemedy: Optional[str] = None
    legalRemedies: Optional[Dict[str, str]] = None
    cantons: List[str] = field(default_factory=list)
    title: Dict[str, str] = field(default_factory=dict)
    uid: Optional[List[str]] = None
    municipalities: Optional[List[Municipality]] = None
    hasSignedPdf: Optional[bool] = None
    secondaryTenants: Optional[Any] = None
    repeatedPublications: Optional[Any] = None
    followUpPublicationTypeCode: Optional[str] = None
    customsStampImages: List = field(default_factory=list)

@dataclass 
class Publication:
    meta: PublicationMeta
    privateMeta: Optional[Any]
    links: List = field(default_factory=list)
    comments: List = field(default_factory=list) 
    attachments: List = field(default_factory=list)
    editFormId: Optional[str] = None
    viewFormId: Optional[str] = None
    version: Optional[int] = None
    content: Optional[Any] = None
    commented: bool = False

@dataclass
class PageRequest:
    sortOrders: List
    page: int
    size: int

@dataclass
class SearchResponse:
    content: List[Publication]
    total: int
    pageRequest: PageRequest

class ShabClient:
    BASE_URL = "https://www.shab.ch/api/v1"
    
    def search(self,
              keyword: str,
              page: int = 0,
              page_size: int = 100,
              include_content: bool = False,
              publication_states: List[PublicationState] = None,
              rubrics: List[str] = None) -> SearchResponse:
        """
        Search publications in SHAB
        
        Args:
            keyword: Search keyword
            page: Page number (0-based)
            page_size: Number of results per page
            include_content: Whether to include full content
            publication_states: List of publication states to include
            rubrics: List of rubrics to search in
            
        Returns:
            SearchResponse containing results
        """
        if publication_states is None:
            publication_states = [PublicationState.PUBLISHED, PublicationState.CANCELLED]
            
        if rubrics is None:
            rubrics = ["AB", "AW", "AZ", "BB", "BH", "EK", "ES", "FM", 
                      "HR", "KK", "LS", "NA", "SB", "SR", "UP", "UV"]
            
        params = {
            "allowRubricSelection": "false",
            "includeContent": str(include_content).lower(),
            "keyword": keyword,
            "pageRequest.page": page,
            "pageRequest.size": page_size,
            "publicationStates": ",".join(s.value for s in publication_states),
            "rubrics": ",".join(rubrics)
        }
        
        try:
            response = requests.get(f"{self.BASE_URL}/publications", params=params)
            response.raise_for_status()
            data = response.json()
            
            # Convert string dates to datetime
            publications = []
            for pub_data in data["content"]:
                # Convert dates in meta
                meta = pub_data["meta"]
                meta["creationDate"] = datetime.fromisoformat(meta["creationDate"].replace("Z", "+00:00"))
                meta["updateDate"] = datetime.fromisoformat(meta["updateDate"].replace("Z", "+00:00"))
                meta["publicationDate"] = datetime.fromisoformat(meta["publicationDate"].replace("Z", "+00:00"))
                if meta.get("expirationDate"):
                    meta["expirationDate"] = datetime.fromisoformat(meta["expirationDate"].replace("Z", "+00:00"))
                
                # Create registration office object
                meta["registrationOffice"] = RegistrationOffice(**meta["registrationOffice"])
                
                # Clean metadata - remove any fields not in PublicationMeta
                valid_fields = PublicationMeta.__annotations__.keys()
                meta = {k: v for k, v in meta.items() if k in valid_fields}
                
                # Create PublicationMeta first
                pub_meta = PublicationMeta(**meta)
                
                # Create Publication with proper structure
                publication = Publication(
                    meta=pub_meta,
                    privateMeta=None,
                    content=pub_data.get("content"),
                    commented=pub_data.get("commented", False)
                )
                publications.append(publication)
                
            return SearchResponse(
                content=publications,
                total=data["total"],
                pageRequest=PageRequest(**data["pageRequest"])
            )
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to search SHAB API: {str(e)}")

    def get_publication(self, publication_id: str) -> Publication:
        """
        Get detailed information about a specific publication
        
        Args:
            publication_id: The UUID of the publication
            
        Returns:
            Publication object with full details
            
        Raises:
            Exception: If publication not found or API error occurs
        """
        try:
            response = requests.get(f"{self.BASE_URL}/publications/{publication_id}")
            response.raise_for_status()
            data = response.json()
            
            # Convert dates in meta
            meta = data["meta"]
            meta["creationDate"] = datetime.fromisoformat(meta["creationDate"].replace("Z", "+00:00"))
            meta["updateDate"] = datetime.fromisoformat(meta["updateDate"].replace("Z", "+00:00"))
            meta["publicationDate"] = datetime.fromisoformat(meta["publicationDate"].replace("Z", "+00:00"))
            if meta.get("expirationDate"):
                meta["expirationDate"] = datetime.fromisoformat(meta["expirationDate"].replace("Z", "+00:00"))
            
            # Convert nested objects
            meta["registrationOffice"] = RegistrationOffice(**meta["registrationOffice"])
            if meta.get("municipalities"):
                meta["municipalities"] = [Municipality(**m) for m in meta["municipalities"]]
            
            data["meta"] = PublicationMeta(**meta)
            return Publication(**data)
            
        except requests.exceptions.RequestException as e:
            if e.response and e.response.status_code == 404:
                raise Exception(f"Publication {publication_id} not found")
            raise Exception(f"Failed to get publication details: {str(e)}")