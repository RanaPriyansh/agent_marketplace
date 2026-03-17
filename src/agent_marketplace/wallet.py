"""
Token wallet integration for Agent Marketplace Protocol.
Uses Hermes wallet tool if available, otherwise simulated local wallet.
"""

import json, os
from pathlib import Path
from typing import Dict, Optional

WALLET_FILE = os.path.expanduser("~/.hermes/wallet.json")

class InsufficientFundsError(Exception):
    """Raised when an agent doesn't have enough tokens."""
    pass

def wallet_transfer(sender: str, dest: str, amount: int) -> bool:
    """
    Transfer tokens from sender to destination.
    Returns True on success, raises InsufficientFundsError on failure.
    """
    # Try to use Hermes wallet tool
    try:
        from hermes_tools import wallet_transfer as hermes_wallet_transfer
        result = hermes_wallet_transfer(sender=sender, dest=dest, amount=amount)
        return result
    except ImportError:
        # Fallback to local wallet simulation
        pass
    
    # Load local wallet
    wallet_data = load_wallet()
    
    # Ensure sender has enough tokens
    sender_balance = wallet_data.get(sender, {}).get("balance", 0)
    if sender_balance < amount:
        raise InsufficientFundsError(f"Sender '{sender}' has {sender_balance} tokens, needs {amount}")
    
    # Update balances
    wallet_data.setdefault(sender, {"balance": 0})["balance"] -= amount
    wallet_data.setdefault(dest, {"balance": 0})["balance"] += amount
    
    # Save wallet
    save_wallet(wallet_data)
    
    return True

def load_wallet() -> Dict:
    """Load wallet data from file."""
    try:
        with open(WALLET_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Initialize with some default balances for testing
        return {
            "agent1": {"balance": 1000},
            "agent2": {"balance": 500},
            "agent3": {"balance": 200},
        }

def save_wallet(data: Dict):
    """Save wallet data to file."""
    Path(WALLET_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(WALLET_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_balance(agent: str) -> int:
    """Get the token balance for an agent."""
    wallet_data = load_wallet()
    return wallet_data.get(agent, {}).get("balance", 0)
