#!/usr/bin/env python3
"""
Test script to verify proxy testing works.
"""
import asyncio
import logging
from tester import ProxyTester

logging.basicConfig(level=logging.DEBUG)

async def main():
    # Known working proxy (test)
    test_proxies = [
        {"ip": "185.162.228.253", "port": 4145, "type": "socks5"},
        {"ip": "51.158.108.135", "port": 59154, "type": "socks5"},
        {"ip": "185.162.229.204", "port": 4145, "type": "socks5"},
    ]
    
    tester = ProxyTester(max_concurrent=5)
    
    print("Testing individual proxies...")
    for proxy in test_proxies:
        print(f"\nTesting {proxy['ip']}:{proxy['port']}...")
        is_working, response_time = await tester.test_proxy(proxy)
        status = "✓ WORKING" if is_working else "✗ NOT WORKING"
        print(f"  {status} - {response_time}ms")
    
    print("\n\nTesting multiple proxies...")
    async def on_test(proxy, is_working, response_time):
        status = "✓" if is_working else "✗"
        print(f"{status} {proxy['ip']}:{proxy['port']} - {response_time}ms")
    
    working = await tester.test_multiple(test_proxies, callback=on_test)
    print(f"\nWorking: {len(working)}")
    for p in working:
        print(f"  {p['ip']}:{p['port']} - {p['response_time']}ms")

if __name__ == "__main__":
    asyncio.run(main())
