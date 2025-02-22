from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum
import uuid

class AccountType(Enum):
    INDIVIDUAL = "individual"
    COMPANY = "company"

class AccountStatus(Enum):
    ACTIVE = "active"
    FROZEN = "frozen"
    CLOSED = "closed"

@dataclass
class AccountOwner:
    name: str
    type: AccountType
    uid: Optional[str] = None  # For companies
    
@dataclass
class BankAccount:
    owner: AccountOwner
    balance: float = 0.0
    status: AccountStatus = AccountStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    freeze_reason: Optional[str] = None

class InMemoryBankAPI:
    def __init__(self):
        self.accounts: Dict[str, BankAccount] = {}

    def list_accounts(self) -> List[BankAccount]:
        """List all accounts"""
        return list(self.accounts.values())

    def create_account(self, owner_name: str, account_type: AccountType, initial_balance: float = 0.0, uid: Optional[str] = None) -> BankAccount:
        """Create a new bank account"""
        owner = AccountOwner(
            name=owner_name,
            type=account_type,
            uid=uid
        )
        
        account = BankAccount(
            owner=owner,
            balance=initial_balance
        )
        
        self._perform_basic_checks(account)
        self.accounts[owner_name] = account
        return account

    def _perform_basic_checks(self, account: BankAccount) -> None:
        """
        Perform basic validation checks on account data
        """
        owner = account.owner
        freeze_reasons = []

        # Basic name check
        if len(owner.name.strip()) < 2:
            freeze_reasons.append("Invalid owner name")

        # Basic company check
        if owner.type == AccountType.COMPANY and not owner.uid:
            freeze_reasons.append("Company requires UID")

        if freeze_reasons:
            self.freeze_account(owner.name, "; ".join(freeze_reasons))

    def get_account(self, owner_name: str) -> Optional[BankAccount]:
        """Get account by owner name"""
        return self.accounts.get(owner_name)

    def freeze_account(self, owner_name: str, reason: str) -> bool:
        """Freeze an account"""
        if account := self.accounts.get(owner_name):
            account.status = AccountStatus.FROZEN
            account.freeze_reason = reason
            return True
        return False

    def unfreeze_account(self, owner_name: str) -> bool:
        """Unfreeze an account"""
        if account := self.accounts.get(owner_name):
            account.status = AccountStatus.ACTIVE
            account.freeze_reason = None
            return True
        return False

# Sample usage
if __name__ == "__main__":
    bank = InMemoryBankAPI()
    
    # Create test accounts
    company_acc = bank.create_account("Test Company AG", AccountType.COMPANY, 1000.0, "CHE-123.456.789")
    individual_acc = bank.create_account("John Doe", AccountType.INDIVIDUAL, 500.0)
    
    print(f"Company account: {company_acc.owner.name}, Balance: {company_acc.balance}")
    print(f"Individual account: {individual_acc.owner.name}, Balance: {individual_acc.balance}")
