#!/usr/bin/env python3
"""Test GeoIP and MTProto scraping."""
import asyncio
from geoip import GeoIP
from mtproto_scraper import MTProtoScraper

async def test_geoip():
    print("=== Testing GeoIP ===")
    geoip = GeoIP(max_concurrent=5)
    
    test_ips = [
        "8.8.8.8",
        "1.1.1.1",
        "185.162.228.253",
    ]
    
    for ip in test_ips:
        country = await geoip.lookup_ip(ip)
        flag = geoip.get_flag(country) if country else '🌐'
        print(f"  {ip} -> {country} {flag}")

async def test_mtproto():
    print("\n=== Testing MTProto Scraper ===")
    scraper = MTProtoScraper()
    proxies = await scraper.scrape_all(debug=True)
    print(f"\nFound {len(proxies)} MTProto proxies")
    for p in proxies[:5]:
        print(f"  {p['server']}:{p['port']} - secret: {p['secret'][:30]}...")

async def main():
    await test_geoip()
    await test_mtproto()

if __name__ == "__main__":
    asyncio.run(main())
