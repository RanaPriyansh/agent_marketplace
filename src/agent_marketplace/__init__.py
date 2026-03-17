"""
Agent Marketplace Protocol (AMP) – Token-based service registry & micro-payment system for Hermes agents.
"""

__version__ = "1.0.0"
from .core import Ledger, Service
from .wallet import wallet_transfer
from .cli import main
