#!/usr/bin/env python3
"""Test full manager update."""
import asyncio
from manager import ProxyManager

async def main():
    manager = ProxyManager(max_proxies=10)
    
    print("Testing full update cycle...\n")
    result = await manager.update(debug=True)
    
    print(f"\n=== Results ===")
    print(f"SOCKS5: {result['socks5']}")
    print(f"MTProto: {result['mtproto']}")
    
    print("\n=== SOCKS5 Proxies ===")
    for p in manager.working_proxies[:5]:
        flag = p.get('flag', '🌐')
        country = p.get('country', 'Unknown')
        print(f"  {flag} {p['ip']}:{p['port']} [{country}] - {p.get('response_time', 0)}ms")
    
    print("\n=== MTProto Proxies ===")
    for p in manager.working_mtproto[:5]:
        flag = p.get('flag', '🌐')
        country = p.get('country', 'Unknown')
        print(f"  {flag} {p['server']}:{p['port']} [{country}] - {p.get('response_time', 0)}ms")

if __name__ == "__main__":
    asyncio.run(main())
