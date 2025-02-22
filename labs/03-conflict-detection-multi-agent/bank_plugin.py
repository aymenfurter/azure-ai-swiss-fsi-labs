from typing import Annotated
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from bank_api import AccountType, AccountStatus
from plugin_logger import log_plugin_call, PluginType
from shared_state import bank_api

class BankPlugin:
    """
    Description: Plugin for managing bank accounts and operations.
    
    Usage:
        kernel.add_plugin(BankPlugin(), plugin_name="bank")
    """
    
    def __init__(self):
        self._client = bank_api  # Use shared instance instead of creating new one
    
    @kernel_function(
        description="Create a new bank account",
        name="create_account"
    )
    def create_account(
        self,
        owner_name: Annotated[str, "Name of the account owner"],
        account_type: Annotated[str, "Type of account (individual/company)"],
        uid: Annotated[str, "Company UID (required for company accounts)"] = ""
    ) -> Annotated[str, "Account creation result or error message"]:
        account_type_enum = AccountType.COMPANY if account_type.lower() == "company" else AccountType.INDIVIDUAL
        
        try:
            account = self._client.create_account(
                owner_name=owner_name,
                account_type=account_type_enum,
                uid=uid if uid else None
            )
            result = (f"Account created:\n"
                   f"ID: {account.id}\n"
                   f"Owner: {account.owner.name}\n"
                   f"Type: {account.owner.type.value}")
        except Exception as e:
            result = f"Error: {str(e)}"
            
        log_plugin_call(
            PluginType.BANK,
            "create_account",
            {"owner_name": owner_name, "account_type": account_type, "uid": uid},
            result
        )
        return result

    @kernel_function(
        description="Get account details",
        name="get_account"
    )
    def get_account(
        self,
        owner_name: Annotated[str, "Name of the account owner"]
    ) -> Annotated[str, "Account details or error message"]:
        account = self._client.get_account(owner_name)
        result = f"No account found for owner {owner_name}" if not account else (
            f"Account Details:\n"
            f"Owner: {account.owner.name}\n"
            f"Type: {account.owner.type.value}\n"
            f"Status: {account.status.value}\n"
            f"Balance: {account.balance}"
        )
        
        log_plugin_call(
            PluginType.BANK,
            "get_account",
            {"owner_name": owner_name},
            result
        )
        return result

    @kernel_function(
        description="Freeze a bank account",
        name="freeze_account"
    )
    def freeze_account(
        self,
        owner_name: Annotated[str, "Name of the account owner"],
        reason: Annotated[str, "Reason for freezing the account"]
    ) -> Annotated[str, "Result of the freeze operation"]:
        try:
            success = self._client.freeze_account(owner_name, reason)
            result = f"Account frozen for {owner_name}: {reason}" if success else f"No account found for {owner_name}"
        except Exception as e:
            result = f"Error freezing account: {str(e)}"
            
        log_plugin_call(
            PluginType.BANK,
            "freeze_account",
            {"owner_name": owner_name, "reason": reason},
            result
        )
        return result

    @kernel_function(
        description="Unfreeze a bank account",
        name="unfreeze_account"
    )
    def unfreeze_account(
        self,
        owner_name: Annotated[str, "Name of the account owner"]
    ) -> Annotated[str, "Result of the unfreeze operation"]:
        try:
            success = self._client.unfreeze_account(owner_name)
            result = f"Account unfrozen for {owner_name}" if success else f"No account found for {owner_name}"
        except Exception as e:
            result = f"Error unfreezing account: {str(e)}"
            
        log_plugin_call(
            PluginType.BANK,
            "unfreeze_account",
            {"owner_name": owner_name},
            result
        )
        return result
