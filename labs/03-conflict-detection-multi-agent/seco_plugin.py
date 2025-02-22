from typing import Annotated
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from seco_api import SecoClient
from plugin_logger import log_plugin_call, PluginType

class SecoPlugin:
    """
    Description: Plugin for checking Swiss sanctions lists.
    
    Usage:
        kernel.add_plugin(SecoPlugin(), plugin_name="seco")
    """
    
    def __init__(self):
        self._client = SecoClient()
    
    @kernel_function(
        description="Check if a person or entity is on the sanctions list",
        name="check_sanctions"
    )
    def check_sanctions(
        self,
        name: Annotated[str, "Name to check against sanctions list"]
    ) -> Annotated[str, "Sanctions check results or error message"]:
        matches = self._client.search(name)
        result = "No sanctions found" if not matches else "SANCTIONS FOUND:\n" + "\n".join([f"- {m}" for m in matches])
        
        log_plugin_call(
            PluginType.SECO,
            "check_sanctions",
            {"name": name},
            result
        )
        return result
