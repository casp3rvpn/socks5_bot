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
    
    TEST_URLS = [
        "https://api.ipify.org?format=json",
        "https://httpbin.org/ip",
    ]
    
    TIMEOUT = 5
    
    def __init__(self, max_concurrent: int = 100):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self._session = None
    
    async def _get_session(self):
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def close(self):
        """Close aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def test_proxy(
        self, 
        proxy: Dict
    ) -> Tuple[bool, float]:
        """Test single proxy with timeout."""
        ip = proxy['ip']
        port = proxy['port']
        start_time = time.time()
        
        try:
            async with self.semaphore:
                connector = ProxyConnector.from_url(f"socks5://{ip}:{port}")
                
                async with aiohttp.ClientSession(connector=connector) as session:
                    request = session.get(self.TEST_URLS[0], timeout=aiohttp.ClientTimeout(total=self.TIMEOUT))
                    response = await asyncio.wait_for(request, timeout=self.TIMEOUT + 1)
                    
                    async with response:
                        if response.status == 200:
                            await response.read()
                            elapsed = (time.time() - start_time) * 1000
                            return True, round(elapsed, 2)
        except asyncio.TimeoutError:
            pass
        except Exception:
            pass
        
        return False, float('inf')
    
    async def test_multiple(
        self, 
        proxies: List[Dict],
        callback=None
    ) -> List[Dict]:
        """Test multiple proxies concurrently with batch processing."""
        working_proxies = []
        batch_size = 100  # Smaller batches to avoid blocking
        
        for i in range(0, len(proxies), batch_size):
            batch = proxies[i:i + batch_size]
            
            async def test_with_callback(proxy: Dict) -> Optional[Dict]:
                is_working, response_time = await self.test_proxy(proxy)
                
                if callback:
                    await callback(proxy, is_working, response_time)
                
                if is_working:
                    result = proxy.copy()
                    result['response_time'] = response_time
                    result['last_checked'] = time.time()
                    return result
                return None
            
            tasks = [test_with_callback(proxy) for proxy in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, dict):
                    working_proxies.append(result)
                elif isinstance(result, Exception) and callback:
                    # Log unexpected errors
                    pass
            
            # Small delay between batches to prevent blocking
            if i + batch_size < len(proxies):
                await asyncio.sleep(0.2)
        
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
