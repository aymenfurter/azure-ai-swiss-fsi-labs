from bank_api import InMemoryBankAPI
from seco_api import SecoClient

# Shared instances
bank_api = InMemoryBankAPI()
seco_client = SecoClient()

# Create some sample accounts for testing
def init_sample_data():
    from bank_api import AccountType
    sanctioned_person = seco_client.get_random_sanctioned_person()
    bank_api.create_account("Test Company AG", AccountType.COMPANY, 1000.0, "CHE-123.456.789")
    bank_api.create_account(sanctioned_person, AccountType.INDIVIDUAL, 500.0)
