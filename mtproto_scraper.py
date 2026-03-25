"""
MTProto proxy scraper - scrapes public MTProto proxy lists.
"""
import re
import asyncio
from typing import List, Dict
import aiohttp
from bs4 import BeautifulSoup


class MTProtoScraper:
    """Scrapes MTProto proxies from public sources."""
    
    # MTProto proxy sources
    SOURCES = [
        "https://raw.githubusercontent.com/ProxyForTelegram/MTProto/master/README.md",
        "https://raw.githubusercontent.com/iamahak/mtproto-proxy/master/README.md",
        "https://raw.githubusercontent.com/pavertom/mtproto-proxy/master/README.md",
        "https://t.me/mtproxy",
        "https://t.me/proxy",
    ]
    
    # MTProto proxy pattern
    # Format: tg://proxy?server=xxx&port=xxx&secret=xxx
    MTProto_PATTERN = re.compile(
        r'tg://proxy\?'
        r'(?:[^&]*&)*'
        r'server=([^&]+)'
        r'(?:[^&]*&)*'
        r'port=(\d+)'
        r'(?:[^&]*&)*'
        r'secret=([^&\s]+)'
    )
    
    # Alternative pattern for direct values
    DIRECT_PATTERN = re.compile(
        r'(?:server|host|ip)[=:\s]+([a-zA-Z0-9.-]+)[\s,]*'
        r'(?:port)[=:\s]+(\d+)[\s,]*'
        r'(?:secret)[=:\s]+([a-zA-Z0-9./-]+)',
        re.IGNORECASE
    )
    
    def __init__(self):
        pass
    
    async def fetch_url(self, session: aiohttp.ClientSession, url: str) -> str:
        """Fetch content from URL."""
        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    return await response.text()
        except Exception:
            pass
        return ""
    
    def parse_tg_link(self, text: str) -> List[Dict]:
        """Parse tg://proxy links from text."""
        proxies = []
        
        for match in self.MTProto_PATTERN.finditer(text):
            server = match.group(1)
            port = match.group(2)
            secret = match.group(3)
            
            try:
                proxies.append({
                    "server": server,
                    "port": int(port),
                    "secret": secret,
                    "type": "mtproto"
                })
            except ValueError:
                continue
        
        return proxies
    
    def parse_direct(self, text: str) -> List[Dict]:
        """Parse direct proxy format."""
        proxies = []
        
        for match in self.DIRECT_PATTERN.finditer(text):
            server = match.group(1)
            port = match.group(2)
            secret = match.group(3)
            
            try:
                proxies.append({
                    "server": server,
                    "port": int(port),
                    "secret": secret,
                    "type": "mtproto"
                })
            except ValueError:
                continue
        
        return proxies
    
    def parse_markdown_table(self, text: str) -> List[Dict]:
        """Parse MTProto proxies from markdown table."""
        proxies = []
        
        # Look for table rows with proxy info
        for line in text.split('\n'):
            if '|' in line:
                parts = line.split('|')
                for part in parts:
                    part = part.strip()
                    
                    # Check for tg:// link
                    proxies.extend(self.parse_tg_link(part))
                    
                    # Check for direct format
                    proxies.extend(self.parse_direct(part))
        
        return proxies
    
    def parse_json_response(self, text: str) -> List[Dict]:
        """Parse JSON proxy list."""
        import json
        proxies = []
        
        try:
            data = json.loads(text)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        server = item.get('server') or item.get('host') or item.get('ip')
                        port = item.get('port')
                        secret = item.get('secret')
                        
                        if server and port and secret:
                            proxies.append({
                                "server": str(server),
                                "port": int(port),
                                "secret": str(secret),
                                "type": "mtproto"
                            })
            elif isinstance(data, dict):
                proxy_list = data.get('proxies', []) or data.get('data', [])
                for item in proxy_list:
                    if isinstance(item, dict):
                        server = item.get('server') or item.get('host')
                        port = item.get('port')
                        secret = item.get('secret')
                        
                        if server and port and secret:
                            proxies.append({
                                "server": str(server),
                                "port": int(port),
                                "secret": str(secret),
                                "type": "mtproto"
                            })
        except json.JSONDecodeError:
            pass
        
        return proxies
    
    async def scrape_source(self, session: aiohttp.ClientSession, url: str) -> List[Dict]:
        """Scrape proxies from a single source."""
        proxies = []
        content = await self.fetch_url(session, url)
        
        if not content:
            return proxies
        
        # Try different parsing methods
        proxies.extend(self.parse_tg_link(content))
        proxies.extend(self.parse_direct(content))
        proxies.extend(self.parse_markdown_table(content))
        proxies.extend(self.parse_json_response(content))
        
        return proxies
    
    async def scrape_all(self, debug: bool = False) -> List[Dict]:
        """Scrape MTProto proxies from all sources."""
        all_proxies = []
        
        async with aiohttp.ClientSession() as session:
            tasks = [self.scrape_source(session, url) for url in self.SOURCES]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                if isinstance(result, list):
                    if debug:
                        print(f"  {self.SOURCES[i]}: found {len(result)} MTProto proxies")
                    all_proxies.extend(result)
                elif debug and isinstance(result, Exception):
                    print(f"  {self.SOURCES[i]}: error - {result}")
        
        # Remove duplicates
        seen = set()
        unique_proxies = []
        for proxy in all_proxies:
            key = f"{proxy['server']}:{proxy['port']}:{proxy['secret']}"
            if key not in seen:
                seen.add(key)
                unique_proxies.append(proxy)
        
        if debug:
            print(f"Total unique MTProto proxies: {len(unique_proxies)}")
        
        return unique_proxies
    
    def scrape_sync(self, debug: bool = False) -> List[Dict]:
        """Synchronous wrapper."""
        return asyncio.run(self.scrape_all(debug=debug))


if __name__ == "__main__":
    scraper = MTProtoScraper()
    proxies = scraper.scrape_sync(debug=True)
    print(f"\nFound {len(proxies)} unique MTProto proxies")
    for p in proxies[:5]:
        print(f"  {p['server']}:{p['port']} - secret: {p['secret'][:20]}...")
