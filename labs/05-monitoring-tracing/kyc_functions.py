import os
import json
from typing import Any, Dict
from dotenv import load_dotenv
from azure.cosmos import CosmosClient
from opentelemetry import trace

load_dotenv(override=True)

tracer = trace.get_tracer(__name__)

def _get_container():
    endpoint = os.environ.get("COSMOS_ENDPOINT")
    key = os.environ.get("COSMOS_KEY")
    db_name = os.environ.get("COSMOS_DB_NAME")
    container_name = os.environ.get("COSMOS_CONTAINER_NAME")

    if not all([endpoint, key, db_name, container_name]):
        raise ValueError("Missing required Cosmos DB environment variables.")

    client = CosmosClient(endpoint, credential=key)
    db = client.get_database_client(db_name)
    container = db.get_container_client(container_name)
    return container

def get_kyc_data(person_name: str) -> str:
    with tracer.start_as_current_span("get_kyc_data") as span:
        span.set_attribute("person_name", person_name)
        try:
            print(f"Searching for KYC record matching '{person_name}'...")
            container = _get_container()
            
            # Split name into parts and create a more flexible search
            name_parts = person_name.lower().split()
            conditions = []
            params = []
            
            for i, part in enumerate(name_parts):
                param_name = f"@name{i}"
                conditions.append(f"CONTAINS(LOWER(c.full_name), {param_name})")
                params.append({"name": param_name, "value": part})
            
            query = f"SELECT * FROM c WHERE {' OR '.join(conditions)}"
            results = list(container.query_items(
                query=query, 
                parameters=params,
                enable_cross_partition_query=True
            ))
            
            if not results:
                return json.dumps({"error": f"No KYC records found matching '{person_name}'."})
            
            # Sort results by relevance (number of matching parts)
            results.sort(key=lambda x: sum(
                part in x['full_name'].lower() 
                for part in name_parts
            ), reverse=True)
            
            # Add trace attributes for query performance
            span.set_attribute("results_count", len(results))
            return json.dumps(results[0], ensure_ascii=False)
        except Exception as e:
            span.set_attribute("error", str(e))
            return json.dumps({"error": f"Exception: {str(e)}"})

def update_kyc_data(person_name: str, updated_data: Dict[str, Any]) -> str:
    with tracer.start_as_current_span("update_kyc_data") as span:
        span.set_attribute("person_name", person_name)
        span.set_attribute("update_fields", list(updated_data.keys()))
        try:
            container = _get_container()
            query = "SELECT * FROM c WHERE CONTAINS(LOWER(c.full_name), LOWER(@person_name))"
            params = [{"name": "@person_name", "value": person_name}]
            results = list(container.query_items(query=query, parameters=params, enable_cross_partition_query=True))
            
            if not results:
                return json.dumps({"error": f"No KYC record found for '{person_name}' to update."})

            record = results[0]
            for key, val in updated_data.items():
                record[key] = val

            container.upsert_item(record)
            return json.dumps({
                "message": f"KYC record updated for {record['full_name']}", 
                "record": record
            }, ensure_ascii=False)
        except Exception as e:
            span.set_attribute("error", str(e))
            return json.dumps({"error": f"Exception: {str(e)}"})