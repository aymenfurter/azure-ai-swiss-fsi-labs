import os
import json
from azure.cosmos import CosmosClient, PartitionKey
from dotenv import load_dotenv

load_dotenv()

def load_kyc_data():
    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                            'data', 'kyc_results_outdated.jsonl')
    kyc_data = []
    
    with open(data_path, 'r') as f:
        for line in f:
            doc = json.loads(line)
            # Create an ID from the full name (lowercase, hyphenated)
            doc['id'] = doc['full_name'].lower().replace(' ', '-')
            kyc_data.append(doc)
    
    return kyc_data

def main():
    endpoint = os.environ["COSMOS_ENDPOINT"]
    key = os.environ["COSMOS_KEY"]
    db_name = os.environ["COSMOS_DB_NAME"]
    container_name = os.environ["COSMOS_CONTAINER_NAME"]

    client = CosmosClient(endpoint, credential=key)
    db = client.create_database_if_not_exists(db_name)
    container = db.create_container_if_not_exists(
        id=container_name,
        partition_key=PartitionKey(path="/id")
    )

    kyc_data = load_kyc_data()
    print(f"Inserting {len(kyc_data)} sample KYC records...")
    for doc in kyc_data:
        container.upsert_item(doc)
        print(f"Upserted record for {doc['full_name']}")
    
    print("Done.")

if __name__ == "__main__":
    main()
