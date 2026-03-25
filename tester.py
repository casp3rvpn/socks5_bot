"""
Proxy tester module - tests SOCKS5 proxies for connectivity and response time.
"""
import asyncio
import time
from typing import List, Dict, Optional, Tuple
import aiohttp
from aiohttp_socks import ProxyConnector


class ProxyTester:
    """Tests SOCKS5 proxies for functionality and measures response time."""
    
    # Test URLs to check proxy connectivity
    TEST_URLS = [
        "https://httpbin.org/ip",
        "https://api.ipify.org?format=json",
        "https://ifconfig.me/ip",
    ]
    
    # Timeout for proxy testing (seconds)
    TIMEOUT = 5
    
    def __init__(self, max_concurrent: int = 50):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def test_proxy(
        self, 
        proxy: Dict, 
        test_url: Optional[str] = None
    ) -> Tuple[bool, float]:
        """
        Test a single proxy.
        
        Returns:
            Tuple of (is_working, response_time_ms)
        """
        url = test_url or self.TEST_URLS[0]
        proxy_addr = f"socks5://{proxy['ip']}:{proxy['port']}"
        
        async with self.semaphore:
            start_time = time.time()
            
            try:
                connector = ProxyConnector.from_url(
                    proxy_addr,
                    timeout=aiohttp.ClientTimeout(total=self.TIMEOUT)
                )
                
                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.get(
                        url,
                        timeout=aiohttp.ClientTimeout(total=self.TIMEOUT)
                    ) as response:
                        if response.status == 200:
                            elapsed = (time.time() - start_time) * 1000  # ms
                            return True, round(elapsed, 2)
                        
            except Exception:
                pass
            
            return False, float('inf')
    
    async def test_proxy_with_retry(
        self, 
        proxy: Dict,
        retries: int = 2
    ) -> Tuple[bool, float]:
        """Test proxy with retries using different test URLs."""
        for i in range(retries):
            test_url = self.TEST_URLS[i % len(self.TEST_URLS)]
            is_working, response_time = await self.test_proxy(proxy, test_url)
            
            if is_working:
                return True, response_time
            
            if i < retries - 1:
                await asyncio.sleep(0.5)
        
        return False, float('inf')
    
    async def test_multiple(
        self, 
        proxies: List[Dict],
        callback=None
    ) -> List[Dict]:
        """
        Test multiple proxies concurrently.
        
        Args:
            proxies: List of proxy dicts
            callback: Optional callback function(proxy, is_working, response_time)
        
        Returns:
            List of working proxies with response time added
        """
        working_proxies = []
        
        async def test_with_callback(proxy: Dict) -> Optional[Dict]:
            is_working, response_time = await self.test_proxy_with_retry(proxy)
            
            if callback:
                await callback(proxy, is_working, response_time)
            
            if is_working:
                result = proxy.copy()
                result['response_time'] = response_time
                result['last_checked'] = time.time()
                return result
            
            return None
        
        tasks = [test_with_callback(proxy) for proxy in proxies]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, dict):
                working_proxies.append(result)
        
        return working_proxies
    
    def test_sync(self, proxies: List[Dict], callback=None) -> List[Dict]:
        """Synchronous wrapper for testing proxies."""
        return asyncio.run(self.test_multiple(proxies, callback))


async def demo_test():
    """Demo function to test the proxy tester."""
    test_proxies = [
        {"ip": "127.0.0.1", "port": 1080, "type": "socks5"},
        {"ip": "185.162.228.253", "port": 4145, "type": "socks5"},
    ]
    
    tester = ProxyTester(max_concurrent=10)
    
    async def on_test(proxy, is_working, response_time):
        status = "✓" if is_working else "✗"
        print(f"{status} {proxy['ip']}:{proxy['port']} - {response_time}ms")
    
    working = await tester.test_multiple(test_proxies, callback=on_test)
    print(f"\nWorking proxies: {len(working)}")
    
    for p in working:
        print(f"  {p['ip']}:{p['port']} - {p['response_time']}ms")


if __name__ == "__main__":
    asyncio.run(demo_test())
