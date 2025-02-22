from typing import Annotated
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from finma_api import FinmaClient
from plugin_logger import log_plugin_call, PluginType

class FinmaPlugin:
    """
    Description: Plugin for searching FINMA registry for insurance intermediaries.
    
    Usage:
        kernel.add_plugin(FinmaPlugin(), plugin_name="finma")
    """
    
    def __init__(self):
        self._client = FinmaClient()
    
    @kernel_function(
        description="Search for insurance intermediaries in FINMA registry",
        name="search_intermediaries"
    )
    def search_intermediaries(
        self,
        query: Annotated[str, "Name of insurance intermediary to search for"]
    ) -> Annotated[str, "List of matching intermediaries or error message"]:
        if not query:
            result = "No search query provided"
        else:
            results = self._client.search(query)
            if not results.Items:
                result = "No insurance intermediaries found"
            else:
                output = []
                for item in results.Items[:5]:
                    output.append(f"Name: {item.Name}")
                    output.append(f"Registration: {item.RegistrationNumber}")
                    output.append(f"Location: {item.LegalSeat}")
                    output.append("---")
                result = "\n".join(output)
            
        log_plugin_call(
            PluginType.FINMA,
            "search_intermediaries",
            {"query": query},
            result
        )
        return result
