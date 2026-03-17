"""
Core Agent Marketplace Protocol (AMP) implementation.
Shared ledger, service registration, token payments, reputation system.
"""

import json, hashlib, time
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from pathlib import Path

# Try to import hermes memory tools, fallback to local storage
try:
    from hermes_tools import memory_query, memory_set
    HERMES_MEMORY_AVAILABLE = True
except ImportError:
    HERMES_MEMORY_AVAILABLE = False
    # Fallback to local JSON file
    import os
    MEMORY_FILE = os.path.expanduser("~/.hermes/memory.json")

@dataclass
class Service:
    """A service offered by an agent."""
    id: int
    owner_agent: str
    service_name: str
    description: str
    price_per_token: int
    endpoint_url: str = ""
    reputation: float = 0.0
    created_at: int = field(default_factory=lambda: int(time.time()))
    success_count: int = 0
    failure_count: int = 0
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Service':
        return cls(**data)


class Ledger:
    """Shared marketplace ledger (global, persistent)."""
    
    def __init__(self, bucket_name: str = "agent_marketplace_ledger"):
        self.bucket = bucket_name
        self._services: Dict[int, Service] = {}
        self._load()
    
    def _load(self):
        """Load ledger from shared memory or local file."""
        raw = None
        if HERMES_MEMORY_AVAILABLE:
            raw = memory_query(self.bucket)
        else:
            try:
                with open(MEMORY_FILE, 'r') as f:
                    data = json.load(f)
                    raw = data.get(self.bucket)
            except (FileNotFoundError, json.JSONDecodeError):
                pass
        
        if raw:
            services_data = json.loads(raw)
            for svc_id, svc_dict in services_data.items():
                self._services[int(svc_id)] = Service.from_dict(svc_dict)
    
    def _save(self):
        """Save ledger to shared memory or local file."""
        services_data = {svc_id: svc.to_dict() for svc_id, svc in self._services.items()}
        json_data = json.dumps(services_data)
        
        if HERMES_MEMORY_AVAILABLE:
            memory_set(self.bucket, json_data)
        else:
            # Ensure directory exists
            Path(MEMORY_FILE).parent.mkdir(parents=True, exist_ok=True)
            # Load existing memory data
            try:
                with open(MEMORY_FILE, 'r') as f:
                    data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                data = {}
            
            data[self.bucket] = json_data
            with open(MEMORY_FILE, 'w') as f:
                json.dump(data, f, indent=2)
    
    def register(self, owner_agent: str, service_name: str, description: str,
                 price: int, endpoint_url: str = "") -> int:
        """Register a new service, returns its ID."""
        # Generate unique ID
        svc_id = int(hashlib.sha1(f"{owner_agent}:{service_name}:{time.time()}".encode()).hexdigest()[:8], 16)
        
        service = Service(
            id=svc_id,
            owner_agent=owner_agent,
            service_name=service_name,
            description=description,
            price_per_token=price,
            endpoint_url=endpoint_url or f"http://localhost:8000/{service_name}",
        )
        
        self._services[svc_id] = service
        self._save()
        return svc_id
    
    def list_services(self) -> List[Dict]:
        """List all registered services."""
        return [svc.to_dict() for svc in self._services.values()]
    
    def get_service(self, service_id: int) -> Optional[Service]:
        """Get a specific service by ID."""
        return self._services.get(service_id)
    
    def request(self, service_id: int, caller_agent: str, amount: int) -> Dict:
        """
        Request a service (pay tokens and get endpoint URL).
        Returns dict with endpoint_url and success status.
        """
        from .wallet import wallet_transfer, InsufficientFundsError
        
        service = self._services.get(service_id)
        if not service:
            raise ValueError(f"Service {service_id} not found")
        
        # Calculate actual price
        total_price = service.price_per_token * amount
        
        # Try to transfer tokens
        try:
            wallet_transfer(
                sender=caller_agent,
                dest=service.owner_agent,
                amount=total_price
            )
        except Exception as e:
            raise InsufficientFundsError(f"Token transfer failed: {e}")
        
        # Update service statistics
        service.success_count += 1
        service.reputation = (service.success_count - service.failure_count) / max(1, service.success_count + service.failure_count)
        self._save()
        
        # Return endpoint URL
        return {
            "endpoint_url": service.endpoint_url,
            "price_paid": total_price,
            "new_balance": "unknown"  # Would need to query wallet
        }
    
    def review(self, service_id: int, reviewer_agent: str, rating: float, comment: str):
        """Leave a review for a service (affects reputation)."""
        service = self._services.get(service_id)
        if not service:
            raise ValueError(f"Service {service_id} not found")
        
        # Update reputation (simple weighted average)
        total_reviews = service.success_count + service.failure_count + 1
        if rating >= 0.7:  # 70% positive
            service.success_count += 1
        else:
            service.failure_count += 1
        
        service.reputation = (service.success_count - service.failure_count) / max(1, service.success_count + service.failure_count)
        self._save()
    
    def get_endpoint(self, service_id: int) -> str:
        """Get the endpoint URL for a service."""
        service = self._services.get(service_id)
        return service.endpoint_url if service else ""
