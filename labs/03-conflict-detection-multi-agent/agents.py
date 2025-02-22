from dataclasses import dataclass
from datetime import datetime
import asyncio
import os
from typing import List, Optional

from semantic_kernel import Kernel
from semantic_kernel.agents.strategies import KernelFunctionSelectionStrategy
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

from seco_plugin import SecoPlugin
from zefix_plugin import ZefixPlugin
from shab_plugin import ShabPlugin
from bank_plugin import BankPlugin
from finma_plugin import FinmaPlugin

# Agent names
KYC_OFFICER = "KYC_Officer"
ACCOUNT_MANAGER = "Account_Manager"
RISK_OFFICER = "Risk_Officer"

def create_kernel() -> Kernel:
    kernel = Kernel()
    
    # Add chat completion service
    service = AzureChatCompletion()
    kernel.add_service(service)
    
    # Add all plugins
    kernel.add_plugin(FinmaPlugin(), plugin_name="finma")
    kernel.add_plugin(SecoPlugin(), plugin_name="seco")
    kernel.add_plugin(ZefixPlugin(), plugin_name="zefix")
    kernel.add_plugin(ShabPlugin(), plugin_name="shab")
    kernel.add_plugin(BankPlugin(), plugin_name="bank")
    
    return kernel

@dataclass
class BankingContext:
    """Shared context between agents"""
    current_customer_name: Optional[str] = None
    current_account_id: Optional[str] = None
    is_company: bool = False
    uid: Optional[str] = None
    risk_level: str = "unknown"
    kyc_status: str = "pending"
    sanctions_hits: List[str] = None