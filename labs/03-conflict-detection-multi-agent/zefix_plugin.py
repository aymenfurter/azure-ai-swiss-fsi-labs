from typing import Annotated
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from zefix_api import ZefixClient
from plugin_logger import log_plugin_call, PluginType

class ZefixPlugin:
    """
    Description: Plugin for accessing Swiss company registry (Zefix).
    
    Usage:
        kernel.add_plugin(ZefixPlugin(), plugin_name="zefix")
        
    Examples:
        {{zefix.search_companies name="Example AG"}} => Returns company matches
    """
    
    def __init__(self):
        self._client = ZefixClient()
    
    @kernel_function(
        description="Search for companies in Swiss commercial registry",
        name="search_companies"
    )
    def search_companies(
        self,
        name: Annotated[str, "Company name to search for"],
        include_deleted: Annotated[bool, "Include deleted companies"] = False
    ) -> Annotated[str, "List of matching companies with details"]:
        """Search for companies in the Zefix registry"""
        if len(name) < 3:
            return "Error: Company name must be at least 3 characters"
            
        result = ""
        try:
            results = self._client.search(
                name=name,
                max_entries=5,
                include_deleted=include_deleted
            )
            
            if not results.list:
                result = "No matching companies found"
            else:
                output = ["Found companies:"]
                for company in results.list:
                    output.append("-" * 40)
                    output.append(f"Name: {company.name}")
                    if company.uidFormatted:
                        output.append(f"UID: {company.uidFormatted}")
                    output.append(f"Status: {company.status}")
                    output.append(f"Location: {company.legalSeat}")
                    if company.cantonalExcerptWeb:
                        output.append(f"Details: {company.cantonalExcerptWeb}")
                        
                if results.hasMoreResults:
                    output.append("-" * 40)
                    output.append(f"Note: Additional results available ({results.maxOffset} total)")
                    
                result = "\n".join(output)
        except Exception as e:
            result = f"Error searching company registry: {str(e)}"
            
        log_plugin_call(
            PluginType.ZEFIX, 
            "search_companies",
            {"name": name, "include_deleted": include_deleted},
            result
        )
        return result
