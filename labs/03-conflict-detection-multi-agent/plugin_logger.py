from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, List
from datetime import datetime
from collections import deque
import json

class PluginType(Enum):
    FINMA = "FINMA"
    SECO = "SECO"
    ZEFIX = "ZEFIX"
    SHAB = "SHAB"
    BANK = "BANK"

@dataclass
class PluginCall:
    plugin_type: PluginType
    function_name: str
    input_data: Dict[str, Any]
    output: str
    timestamp: str

# Store last N plugin calls
_call_history = deque(maxlen=50)

def log_plugin_call(plugin_type: PluginType, function_name: str, input_data: Dict[str, Any], output: str) -> None:
    """Log a plugin function call with its inputs and outputs"""
    call = PluginCall(
        plugin_type=plugin_type,
        function_name=function_name,
        input_data=input_data,
        output=output,
        timestamp=datetime.now().isoformat()
    )
    _call_history.append(call)

def get_last_calls(limit: int = 10) -> List[PluginCall]:
    """Get the most recent plugin calls"""
    return list(reversed(list(_call_history)))[:limit]
