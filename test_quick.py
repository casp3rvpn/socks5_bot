#!/usr/bin/env python3
"""Quick test to verify proxy testing works."""
import asyncio
import time
from tester import ProxyTester

async def main():
    # Test with known proxies
    test_proxies = [
        {"ip": "185.162.228.253", "port": 4145, "type": "socks5"},
        {"ip": "51.158.108.135", "port": 59154, "type": "socks5"},
        {"ip": "185.162.229.204", "port": 4145, "type": "socks5"},
        {"ip": "185.162.228.125", "port": 4145, "type": "socks5"},
        {"ip": "185.162.230.79", "port": 4145, "type": "socks5"},
    ]
    
    tester = ProxyTester(max_concurrent=5)
    
    print(f"Testing {len(test_proxies)} proxies...")
    start = time.time()
    
    async def on_test(proxy, is_working, response_time):
        status = "✓" if is_working else "✗"
        print(f"{status} {proxy['ip']}:{proxy['port']} - {response_time}ms")
    
    working = await tester.test_multiple(test_proxies, callback=on_test)
    elapsed = time.time() - start
    
    print(f"\nDone in {elapsed:.1f}s")
    print(f"Working: {len(working)}")
    for p in working:
        print(f"  {p['ip']}:{p['port']} - {p['response_time']}ms")

if __name__ == "__main__":
    asyncio.run(main())
