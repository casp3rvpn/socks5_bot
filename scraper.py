"""
Proxy scraper module - scrapes public SOCKS5 proxy lists from various sources.
"""
import re
import asyncio
from typing import List, Dict
import aiohttp
from bs4 import BeautifulSoup


class ProxyScraper:
    """Scrapes SOCKS5 proxies from multiple public sources."""
    
    # List of public proxy sources - raw lists
    SOURCES = [
        "https://www.proxy-list.download/api/v1/get?type=socks5",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks5.txt",
        "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/socks5/data.txt",
        "https://raw.githubusercontent.com/HyperBeast/proxy-list/main/socks5.txt",
        "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
        "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt",
        "https://raw.githubusercontent.com/UserR3X/proxy-list/main/online/socks5.txt",
        "https://raw.githubusercontent.com/proxy4parsing/proxy/main/socks5.txt",
        "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS5_RAW.txt",
    ]
    
    SCRAPE_URLS = [
        "https://spys.me/socks.txt",
        "https://www.socks-proxy.net/",
    ]
    
    # API endpoints that return JSON
    API_URLS = [
        "https://proxylist.geonode.com/api/proxy-list?limit=500&protocols=socks5&sort_by=lastChecked&sort_type=desc",
        "https://api.proxyscrape.com/v2/?request=get&protocol=socks5&timeout=10000&country=all&ssl=all&anonymity=all",
    ]
    
    def __init__(self):
        self.ip_pattern = re.compile(
            r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
            r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
        )
        self.port_pattern = re.compile(r':(\d+)')
    
    async def fetch_url(self, session: aiohttp.ClientSession, url: str) -> str:
        """Fetch content from URL."""
        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    return await response.text()
        except Exception:
            pass
        return ""
    
    def parse_ip_port(self, line: str) -> List[Dict]:
        """Parse IP:PORT format from a line."""
        proxies = []
        # Match IP:PORT pattern
        matches = re.findall(
            r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})',
            line
        )
        for ip, port in matches:
            try:
                port_num = int(port)
                if 1 <= port_num <= 65535:
                    proxies.append({
                        "ip": ip,
                        "port": port_num,
                        "type": "socks5"
                    })
            except ValueError:
                continue
        return proxies
    
    def parse_html_table(self, html: str) -> List[Dict]:
        """Parse proxy table from HTML."""
        proxies = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Try to find table rows
        for table in soup.find_all('table'):
            for row in table.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) >= 2:
                    try:
                        ip_port = cells[0].get_text().strip()
                        proxy_type = cells[1].get_text().strip().lower()
                        
                        if 'socks5' in proxy_type or len(cells) < 5:
                            matches = re.findall(
                                r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})',
                                ip_port
                            )
                            for ip, port in matches:
                                port_num = int(port)
                                if 1 <= port_num <= 65535:
                                    proxies.append({
                                        "ip": ip,
                                        "port": port_num,
                                        "type": "socks5"
                                    })
                    except Exception:
                        continue
        
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
                        ip = item.get('ip') or item.get('proxy_ip') or item.get('Ip') or item.get('IP')
                        port = item.get('port') or item.get('proxy_port') or item.get('Port') or item.get('PORT')
                        protocol = str(item.get('protocol', '') or item.get('Protocol', '')).lower()
                        
                        if ip and port and 'socks5' in protocol:
                            try:
                                proxies.append({
                                    "ip": str(ip),
                                    "port": int(port),
                                    "type": "socks5"
                                })
                            except (ValueError, TypeError):
                                continue
                    elif isinstance(item, str):
                        # Handle simple IP:PORT strings in list
                        proxies.extend(self.parse_ip_port(item))
            elif isinstance(data, dict):
                proxy_list = data.get('proxies', []) or data.get('data', [])
                for item in proxy_list:
                    if isinstance(item, dict):
                        ip = item.get('ip') or item.get('proxy_ip') or item.get('Ip')
                        port = item.get('port') or item.get('proxy_port') or item.get('Port')
                        protocol = str(item.get('protocol', '') or item.get('Protocol', '')).lower()
                        
                        if ip and port and 'socks5' in protocol:
                            try:
                                proxies.append({
                                    "ip": str(ip),
                                    "port": int(port),
                                    "type": "socks5"
                                })
                            except (ValueError, TypeError):
                                continue
        except json.JSONDecodeError:
            # Try parsing as plain text (IP:PORT per line)
            for line in text.strip().split('\n'):
                proxies.extend(self.parse_ip_port(line))
        return proxies
    
    async def scrape_source(self, session: aiohttp.ClientSession, url: str) -> List[Dict]:
        """Scrape proxies from a single source."""
        proxies = []
        content = await self.fetch_url(session, url)
        
        if not content:
            return proxies
        
        # Try JSON parsing first
        proxies.extend(self.parse_json_response(content))
        
        # Try HTML table parsing
        proxies.extend(self.parse_html_table(content))
        
        # Try simple IP:PORT pattern matching
        for line in content.split('\n'):
            proxies.extend(self.parse_ip_port(line))
        
        return proxies
    
    async def scrape_all(self, debug: bool = False) -> List[Dict]:
        """Scrape proxies from all sources."""
        all_proxies = []
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            urls = self.SOURCES + self.SCRAPE_URLS + self.API_URLS
            
            for url in urls:
                tasks.append(self.scrape_source(session, url))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                if isinstance(result, list):
                    if debug:
                        print(f"  {urls[i]}: found {len(result)} proxies")
                    all_proxies.extend(result)
                elif debug and isinstance(result, Exception):
                    print(f"  {urls[i]}: error - {result}")
        
        # Remove duplicates
        seen = set()
        unique_proxies = []
        for proxy in all_proxies:
            key = f"{proxy['ip']}:{proxy['port']}"
            if key not in seen:
                seen.add(key)
                unique_proxies.append(proxy)
        
        if debug:
            print(f"Total unique proxies: {len(unique_proxies)}")
        
        return unique_proxies
    
    def scrape_sync(self) -> List[Dict]:
        """Synchronous wrapper for scraping."""
        return asyncio.run(self.scrape_all())


if __name__ == "__main__":
    scraper = ProxyScraper()
    proxies = scraper.scrape_sync()
    print(f"Found {len(proxies)} unique SOCKS5 proxies")
    for p in proxies[:10]:
        print(f"  {p['ip']}:{p['port']}")
