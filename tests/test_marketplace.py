"""
Tests for Agent Marketplace Protocol.
"""

import pytest
import tempfile
import os
import json
from pathlib import Path

# Set up test environment
os.environ["HERMES_AGENT_ID"] = "test_agent"

def test_ledger_basic():
    """Test basic ledger operations."""
    from agent_marketplace.core import Ledger
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test ledger with local storage
        os.environ["HOME"] = tmpdir
        ledger = Ledger(bucket_name="test_ledger")
        
        # Register a service
        svc_id = ledger.register(
            owner_agent="agent1",
            service_name="pdf_summariser",
            description="Summarises PDF files",
            price=5,
            endpoint_url="http://localhost:8000/summarise"
        )
        
        assert svc_id > 0
        
        # List services
        services = ledger.list_services()
        assert len(services) == 1
        assert services[0]["service_name"] == "pdf_summariser"
        assert services[0]["owner_agent"] == "agent1"
        assert services[0]["price_per_token"] == 5
        
        # Get service
        service = ledger.get_service(svc_id)
        assert service is not None
        assert service.endpoint_url == "http://localhost:8000/summarise"

def test_wallet_transfer():
    """Test token transfer."""
    from agent_marketplace.wallet import wallet_transfer, load_wallet, get_balance
    
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["HOME"] = tmpdir
        
        # Initialize wallet
        wallet_data = {
            "agent1": {"balance": 100},
            "agent2": {"balance": 50}
        }
        wallet_file = os.path.join(tmpdir, ".hermes", "wallet.json")
        os.makedirs(os.path.dirname(wallet_file), exist_ok=True)
        with open(wallet_file, 'w') as f:
            json.dump(wallet_data, f)
        
        # Test transfer
        result = wallet_transfer("agent1", "agent2", 30)
        assert result is True
        
        # Check balances
        assert get_balance("agent1") == 70
        assert get_balance("agent2") == 80
        
        # Test insufficient funds
        from agent_marketplace.wallet import InsufficientFundsError
        with pytest.raises(InsufficientFundsError):
            wallet_transfer("agent1", "agent2", 100)  # agent1 only has 70

def test_service_request():
    """Test requesting a service with token payment."""
    from agent_marketplace.core import Ledger
    from agent_marketplace.wallet import wallet_transfer, get_balance
    
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["HOME"] = tmpdir
        
        # Setup wallet
        wallet_file = os.path.join(tmpdir, ".hermes", "wallet.json")
        os.makedirs(os.path.dirname(wallet_file), exist_ok=True)
        with open(wallet_file, 'w') as f:
            json.dump({"caller": {"balance": 100}, "owner": {"balance": 0}}, f)
        
        # Register service
        ledger = Ledger(bucket_name="test_request")
        svc_id = ledger.register(
            owner_agent="owner",
            service_name="test_service",
            description="Test service",
            price=10
        )
        
        # Request service
        result = ledger.request(svc_id, "caller", 1)
        assert "endpoint_url" in result
        assert result["price_paid"] == 10
        
        # Check balances
        assert get_balance("caller") == 90
        assert get_balance("owner") == 10

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
