from io import BufferedReader
import os
import uuid
import time
import json
import logging
import requests
from typing import Dict, List, Optional, Union, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContentUnderstandingClient:
    def __init__(self, endpoint: str = None, api_key: str = None):
        """Initialize the Content Understanding client."""
        self.endpoint = endpoint or os.environ.get("CONTENT_UNDERSTANDING_AI_ENDPOINT", "").rstrip('/')
        self.api_key = api_key or os.environ.get("CONTENT_UNDERSTANDING_AI_KEY", "")
        self.api_version = "2024-12-01-preview"
        
        if not self.endpoint or not self.api_key:
            raise ValueError("Endpoint and API key must be provided or set in environment variables")

    def delete_analyzer(self, analyzer_id: str) -> bool:
        """Delete an existing analyzer."""
        url = f"{self.endpoint}/contentunderstanding/analyzers/{analyzer_id}?api-version={self.api_version}"
        headers = self._get_headers()
        
        try:
            resp = requests.delete(url, headers=headers)
            if resp.status_code == 404:
                return False
            resp.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            logging.warning(f"Error deleting analyzer {analyzer_id}: {str(e)}")
            return False

    def create_analyzer(self, schema: Dict[str, Any], force_recreate: bool = True) -> Dict[str, Any]:
        """Create or update an analyzer with the given schema."""
        analyzer_id = schema["name"]
        url = f"{self.endpoint}/contentunderstanding/analyzers/{analyzer_id}?api-version={self.api_version}"
        
        analyzer_config = self._build_analyzer_config(schema)
        headers = self._get_headers()
        
        # Debug output
        logger.debug("Creating analyzer with config:")
        logger.debug(json.dumps(analyzer_config, indent=2))
        
        if force_recreate:
            # Delete existing analyzer if it exists
            self.delete_analyzer(analyzer_id)
            time.sleep(2)
        
        resp = requests.put(url, headers=headers, json=analyzer_config)
        resp.raise_for_status()
        return resp.json()

    def analyze_content(self, analyzer_id: str, content: Union[bytes, BufferedReader]) -> Dict[str, Any]:
        """Analyze content using the specified analyzer.
        
        Args:
            analyzer_id (str): The ID of the analyzer to use
            content (Union[bytes, BufferedReader]): The content to analyze, either as bytes or a file buffer
        """
        url = f"{self.endpoint}/contentunderstanding/analyzers/{analyzer_id}:analyze?_overload=analyzeBinary&api-version={self.api_version}"
        
        headers = self._get_headers({
            "Content-Type": "application/octet-stream",
            "Operation-Id": str(uuid.uuid4()),
            "x-ms-client-request-id": str(uuid.uuid4())
        })
        
        # If content is a file buffer, read it entirely
        if hasattr(content, 'read'):
            content = content.read()
        
        resp = requests.post(url, headers=headers, data=content)
        
        if resp.status_code == 202:
            operation_url = resp.headers.get("Operation-Location")
            if not operation_url:
                raise ValueError("No Operation-Location header in async response")
            return self._poll_operation(operation_url)
        
        resp.raise_for_status()
        return resp.json()

    def _poll_operation(self, operation_url: str, max_tries: int = 240, delay: int = 2) -> Dict[str, Any]:
        """Poll an async operation until completion."""
        for attempt in range(max_tries):
            logging.debug(f"Polling attempt {attempt + 1}/{max_tries}")
            resp = requests.get(operation_url, headers={"Ocp-Apim-Subscription-Key": self.api_key})
            resp.raise_for_status()
            
            result = resp.json()
            status = result.get("status", "").lower()
            
            if status == "succeeded":
                return result.get("result", {})
            elif status in ["failed", "canceled"]:
                raise RuntimeError(f"Operation {status}: {result.get('error', {}).get('message', 'Unknown error')}")
            elif status in ["notstarted", "running"]:
                time.sleep(delay)
                continue
            else:
                raise RuntimeError(f"Unknown status: {status}")
        
        raise TimeoutError("Operation timed out")

    def _build_analyzer_config(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Build the analyzer configuration from a schema."""
        fields = {}
        for field in schema["fields"]:
            field_name = field["name"]
            field_config = {
                "type": field["type"],
                "description": field.get("description", "")
            }
            
            # Only add method if not an array type
            if field["type"] != "array":
                field_config["method"] = field.get("method", "generate")
            
            # Handle enum fields
            if "enum" in field:
                field_config["enum"] = field["enum"]
                field_config["method"] = "classify"
            
            if field["type"] == "array":
                items_config = field.get("items", {})
                
                if items_config.get("type") == "object":
                    properties = {}
                    for prop_name, prop_config in items_config.get("properties", {}).items():
                        properties[prop_name] = {
                            "type": prop_config.get("type", "string")
                        }
                    
                    field_config["items"] = {
                        "type": "object",
                        "properties": properties
                    }
                else:
                    field_config["items"] = {
                        "type": "string"
                    }
            
            fields[field_name] = field_config

        return {
            "analyzerId": schema["name"],
            "description": schema.get("description", ""),
            "scenario": schema.get("scenario", "text"),
            "fieldSchema": {
                "fields": fields
            },
            "config": {
                "locales": schema.get("config", {}).get("locales", []),
                "returnDetails": schema.get("config", {}).get("returnDetails", True)
            }
        }

    def _get_headers(self, additional_headers: Dict[str, str] = None) -> Dict[str, str]:
        """Get the headers for API requests."""
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Content-Type": "application/json"
        }
        if additional_headers:
            headers.update(additional_headers)
        return headers