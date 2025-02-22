from typing import Annotated
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from shab_api import ShabClient, PublicationState
from plugin_logger import log_plugin_call, PluginType

class ShabPlugin:
    """
    Description: Plugin for searching Swiss Official Gazette (SHAB) publications.
    
    Usage:
        kernel.add_plugin(ShabPlugin(), plugin_name="shab")
        
    Examples:
        {{shab.search_publications keyword="Example AG"}} => Returns latest publications
    """
    
    def __init__(self):
        self._client = ShabClient()
    
    @kernel_function(
        description="Search for company-related publications in SHAB gazette",
        name="search_publications"
    )
    def search_publications(
        self,
        keyword: Annotated[str, "Company name or keyword to search for"],
        rubric: Annotated[str, "Publication type (HR=Commercial Registry, BB=Bankruptcy, etc)"] = "HR"
    ) -> Annotated[str, "List of relevant publications"]:
        """Search official publications for company information"""
        result = ""
        if not keyword:
            result = "Error: Search keyword is required"
            log_plugin_call(
                PluginType.SHAB,
                "search_publications",
                {"keyword": keyword, "rubric": rubric},
                result
            )
            return result
            
        try:
            results = self._client.search(
                keyword=keyword,
                publication_states=[PublicationState.PUBLISHED],
                rubrics=[rubric] if rubric else None,
                page_size=5
            )
            
            if not results.content:
                result = f"No publications found for '{keyword}'"
                log_plugin_call(
                    PluginType.SHAB,
                    "search_publications",
                    {"keyword": keyword, "rubric": rubric},
                    result
                )
                return result
                
            output = [f"Publications for '{keyword}':"]
            
            for pub in results.content:
                meta = pub.meta
                output.append("=" * 40)
                
                # Add publication title
                title = meta.title.get('en') or meta.title.get('de') or "No title"
                output.append(f"Title: {title}")
                
                # Add key details
                output.append(f"Date: {meta.publicationDate.strftime('%Y-%m-%d')}")
                output.append(f"Type: {meta.rubric}")
                
                # Add location info if available
                if meta.municipalities:
                    location = meta.municipalities[0]
                    output.append(f"Location: {location.town} ({location.swissZipCode})")
                
                # Add company UID if available
                if meta.uid:
                    output.append(f"UID: {meta.uid[0]}")
                
            if results.total > len(results.content):
                output.append(f"\nNote: {results.total - len(results.content)} more results available")
                
            result = "\n".join(output)
            
        except Exception as e:
            result = f"Error searching publications: {str(e)}"
            
        log_plugin_call(
            PluginType.SHAB,
            "search_publications",
            {"keyword": keyword, "rubric": rubric},
            result
        )
        return result
