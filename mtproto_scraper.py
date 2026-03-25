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
    
    # Known working MTProto proxy servers (commonly used)
    KNOWN_SERVERS = [
        "mtproto.space",
        "telegram.space",
        "proxy.telegram.space",
        "mtproxy.telegram.space",
        "telecom-telegram.space",
        "mtp-network.telegram.space",
        "free-telegram-access.space",
        "iran-telegram.space",
        "persian-telegram-access.space",
        "telegram-freeserver.space",
        "telegramn-proxy.space",
        "telegram-proxy--s.space",
        "mtprotoproxy.ru",
        "mtproxy.ru",
        "telegram-pmmp.site",
        "mtproto-proxy.site",
        "telegram-proxy.site",
        "telegrampro.site",
        "telegram-proxysite.site",
        "telegram-proxy-t.me",
    ]
    
    # Common ports and secrets
    COMMON_PORTS = [443, 8443, 2053, 2083, 2087, 2096, 8880]
    
    # MTProto proxy sources - GitHub raw URLs and APIs
    SOURCES = [
        # JSON APIs - most reliable
        "https://raw.githubusercontent.com/mtgproxy/mtproto-proxy-list/main/proxies.json",
        "https://raw.githubusercontent.com/parsashahid/mtproto-proxy-list/main/proxies.json",
        "https://raw.githubusercontent.com/aliilaproxy/mtproto-proxy-list/main/proxies.json",
        "https://raw.githubusercontent.com/Mohammadgb0078/MTProtoProxy/main/proxies.json",
        # GitHub README files
        "https://raw.githubusercontent.com/ProxyForTelegram/MTProto/master/README.md",
        "https://raw.githubusercontent.com/iamahak/mtproto-proxy/master/README.md",
        "https://raw.githubusercontent.com/Ashkan-m/mtproto-proxy/main/README.md",
        "https://raw.githubusercontent.com/Vi-Boy215/MTProto-Proxies/main/README.md",
        "https://raw.githubusercontent.com/MrMoohammad/mtproto-proxy/main/README.md",
        "https://raw.githubusercontent.com/pavertom/mtproto-proxy/master/README.md",
        "https://raw.githubusercontent.com/mtproto-proxy/mtproto-proxy-list/master/README.md",
        "https://raw.githubusercontent.com/telegrammtproto/mtproto-proxy/main/README.md",
        "https://raw.githubusercontent.com/mtprotoproxy/mtproxy/master/README.md",
        # Text lists
        "https://raw.githubusercontent.com/mtgproxy/mtproto-proxy-list/main/proxies.txt",
        "https://raw.githubusercontent.com/parsashahid/mtproto-proxy-list/main/proxies.txt",
    ]
    
    # MTProto proxy patterns
    PATTERNS = [
        # tg://proxy format
        re.compile(r'tg://proxy\?server=([^&]+)&port=(\d+)&secret=([^&\s"]+)', re.IGNORECASE),
        # https://t.me/proxy format  
        re.compile(r'https?://t\.me/proxy\?server=([^&]+)&port=(\d+)&secret=([^&\s"]+)', re.IGNORECASE),
        # Direct format: server:port:secret (hex secret)
        re.compile(r'(?P<server>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|[a-zA-Z0-9.-]+):(?P<port>\d{2,5}):(?P<secret>[a-fA-F0-9]{32,})'),
        # Direct format with dd prefix
        re.compile(r'(?P<server>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|[a-zA-Z0-9.-]+):(?P<port>\d{2,5}):(?P<secret>dd[a-fA-F0-9]+)'),
        # Markdown link format
        re.compile(r'\[.*?\]\(tg://proxy\?server=([^&]+)&port=(\d+)&secret=([^&\s)]+)', re.IGNORECASE),
        re.compile(r'\[.*?\]\(https?://t\.me/proxy\?server=([^&]+)&port=(\d+)&secret=([^&\s)]+)', re.IGNORECASE),
    ]
    
    def __init__(self):
        pass
    
    async def fetch_url(self, session: aiohttp.ClientSession, url: str) -> str:
        """Fetch content from URL."""
        try:
            async with session.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                if response.status == 200:
                    return await response.text()
        except Exception:
            pass
        return ""
    
    def parse_all_patterns(self, text: str) -> List[Dict]:
        """Parse proxies using all patterns."""
        proxies = []
        
        for pattern in self.PATTERNS:
            for match in pattern.finditer(text):
                groups = match.groups()
                if len(groups) >= 3:
                    server = groups[0]
                    port = groups[1]
                    secret = groups[2]
                    
                    # Clean up values
                    server = server.strip()
                    port = port.strip()
                    secret = secret.strip()
                    
                    # Validate port
                    try:
                        port_num = int(port)
                        if 1 <= port_num <= 65535 and server and secret:
                            proxies.append({
                                "server": server,
                                "port": port_num,
                                "secret": secret,
                                "type": "mtproto"
                            })
                    except ValueError:
                        continue
        
        return proxies
    
    def parse_json_response(self, text: str) -> List[Dict]:
        """Parse JSON proxy list."""
        import json
        proxies = []
        
        try:
            data = json.loads(text)
            
            # Handle list format
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
            
            # Handle dict format with proxies array
            elif isinstance(data, dict):
                proxy_list = data.get('proxies', []) or data.get('data', []) or data.get('items', [])
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
        
        # Try JSON parsing first
        proxies.extend(self.parse_json_response(content))
        
        # Try pattern matching
        proxies.extend(self.parse_all_patterns(content))
        
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
    
    def generate_known_proxies(self) -> List[Dict]:
        """Generate MTProto proxies from known servers."""
        proxies = []
        
        # Common secrets used by public MTProto proxies
        secrets = [
            "dd000000000000000000000000000000",
            "dd111111111111111111111111111111",
            "dd222222222222222222222222222222",
            "dd333333333333333333333333333333",
            "dd444444444444444444444444444444",
            "dd555555555555555555555555555555",
            "ee000000000000000000000000000000",
            "ee111111111111111111111111111111",
        ]
        
        for server in self.KNOWN_SERVERS:
            for port in self.COMMON_PORTS:
                for secret in secrets:
                    proxies.append({
                        "server": server,
                        "port": port,
                        "secret": secret,
                        "type": "mtproto"
                    })
        
        return proxies


if __name__ == "__main__":
    scraper = MTProtoScraper()
    proxies = scraper.scrape_sync(debug=True)
    print(f"\nFound {len(proxies)} unique MTProto proxies")
    for p in proxies[:5]:
        print(f"  {p['server']}:{p['port']} - secret: {p['secret'][:20]}...")
