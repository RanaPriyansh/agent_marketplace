#!/usr/bin/env python3
"""
CLI for Agent Marketplace Protocol (AMP).
Register services, list marketplace, request services, leave reviews.
"""

import argparse, sys, json, os, textwrap

def main():
    parser = argparse.ArgumentParser(
        prog="agent-marketplace",
        description="🛠️  Agent Marketplace – discover, pay for, and review agent services."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # ---- register -------------------------------------------------
    reg = sub.add_parser("register", help="Publish a new service")
    reg.add_argument("service_name", help="Short name of the capability")
    reg.add_argument("--desc", help="One-line description", default="")
    reg.add_argument("--price", type=int, help="Price in tokens per use", default=1)
    reg.add_argument("--endpoint", help="Service endpoint URL (optional)", default="")
    reg.add_argument("--agent", help="Your agent ID", default=os.environ.get("HERMES_AGENT_ID", "agent1"))

    # ---- list ----------------------------------------------------
    list_cmd = sub.add_parser("list", help="List all published services")
    list_cmd.add_argument("--json", action="store_true", help="Output as JSON")

    # ---- request ------------------------------------------------
    req = sub.add_parser("request", help="Call a service (pay tokens)")
    req.add_argument("service_id", type=int, help="ID of the service to call")
    req.add_argument("--agent", help="Your agent ID", default=os.environ.get("HERMES_AGENT_ID", "agent1"))
    req.add_argument("--tokens", type=int, help="How many tokens to spend", default=1)

    # ---- review -------------------------------------------------
    rev = sub.add_parser("review", help="Leave feedback on a service")
    rev.add_argument("service_id", type=int, help="ID of the service to review")
    rev.add_argument("--rating", type=float, required=True, help="0.0-1.0 rating (0=bad, 1=good)")
    rev.add_argument("--comment", required=True, help="Free-form comment")
    rev.add_argument("--agent", help="Your agent ID", default=os.environ.get("HERMES_AGENT_ID", "agent1"))

    # ---- balance ------------------------------------------------
    bal = sub.add_parser("balance", help="Check token balance")
    bal.add_argument("--agent", help="Your agent ID", default=os.environ.get("HERMES_AGENT_ID", "agent1"))

    args = parser.parse_args()

    # Import core module
    from .core import Ledger
    ledger = Ledger()

    if args.cmd == "register":
        service_id = ledger.register(
            owner_agent=args.agent,
            service_name=args.service_name,
            description=args.desc,
            price=args.price,
            endpoint_url=args.endpoint
        )
        print(f"✅ Service '{args.service_name}' registered (id={service_id})")
        print(f"   Endpoint: {ledger.get_endpoint(service_id)}")

    elif args.cmd == "list":
        services = ledger.list_services()
        if args.json:
            print(json.dumps(services, indent=2))
        else:
            if not services:
                print("No services registered yet.")
            else:
                print(f"{'ID':<8} {'Owner':<15} {'Service':<20} {'Price':<8} {'Reputation':<12} {'Endpoint'}")
                print("-" * 80)
                for svc in services:
                    print(f"{svc['id']:<8} {svc['owner_agent']:<15} {svc['service_name']:<20} {svc['price_per_token']:<8} {svc['reputation']:<12.3f} {svc['endpoint_url']}")

    elif args.cmd == "request":
        try:
            result = ledger.request(args.service_id, args.agent, args.tokens)
            print(f"✅ Service requested successfully!")
            print(f"   Price paid: {result['price_paid']} tokens")
            print(f"   Endpoint URL: {result['endpoint_url']}")
            print(f"   You can now call the service at the endpoint above.")
        except Exception as e:
            print(f"❌ Request failed: {e}")
            sys.exit(1)

    elif args.cmd == "review":
        try:
            ledger.review(args.service_id, args.agent, args.rating, args.comment)
            print(f"✅ Review submitted for service {args.service_id}")
        except Exception as e:
            print(f"❌ Review failed: {e}")
            sys.exit(1)

    elif args.cmd == "balance":
        from .wallet import get_balance
        balance = get_balance(args.agent)
        print(f"Agent '{args.agent}' balance: {balance} tokens")

if __name__ == "__main__":
    main()
