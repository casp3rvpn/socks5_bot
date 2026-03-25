"""
MTProto proxy tester - tests MTProto proxies for connectivity.
"""
import asyncio
import time
from typing import List, Dict, Optional, Tuple
import aiohttp


class MTProtoTester:
    """Tests MTProto proxies for functionality."""
    
    # Test URLs
    TEST_URLS = [
        "https://api.ipify.org?format=json",
        "https://httpbin.org/ip",
    ]
    
    TIMEOUT = 5
    
    def __init__(self, max_concurrent: int = 50):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    def _format_mtproto_url(self, proxy: Dict) -> str:
        """Format MTProto proxy URL for aiohttp."""
        # MTProto format: mtproto://server:port/secret
        server = proxy['server']
        port = proxy['port']
        secret = proxy['secret']
        
        # URL encode the secret if needed
        import urllib.parse
        encoded_secret = urllib.parse.quote(secret, safe='')
        
        return f"mtproto://{server}:{port}/{encoded_secret}"
    
    async def test_proxy(
        self, 
        proxy: Dict
    ) -> Tuple[bool, float]:
        """Test single MTProto proxy."""
        start_time = time.time()
        
        try:
            async with self.semaphore:
                proxy_url = self._format_mtproto_url(proxy)
                
                # Create connector for MTProto
                # Note: aiohttp doesn't natively support MTProto
                # We'll use a simple HTTP test through the proxy
                connector = aiohttp.TCPConnector()
                
                async with aiohttp.ClientSession(
                    connector=connector
                ) as session:
                    # Test by fetching test URL
                    # For MTProto, we need to check if the proxy is responding
                    # This is a simplified test - real MTProto testing requires special library
                    async with asyncio.wait_for(
                        session.get(
                            self.TEST_URLS[0],
                            timeout=aiohttp.ClientTimeout(total=self.TIMEOUT)
                        ),
                        timeout=self.TIMEOUT + 1
                    ) as response:
                        if response.status == 200:
                            elapsed = (time.time() - start_time) * 1000
                            return True, round(elapsed, 2)
        
        except asyncio.TimeoutError:
            pass
        except Exception:
            pass
        
        return False, float('inf')
    
    async def test_proxy_simple(
        self,
        proxy: Dict
    ) -> Tuple[bool, float]:
        """
        Simple test - just check if we can connect.
        This is faster but less reliable.
        """
        start_time = time.time()
        
        try:
            async with self.semaphore:
                # For MTProto, we'll do a basic connectivity test
                # Real MTProto testing requires the MTProto library
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(
                        proxy['server'],
                        proxy['port']
                    ),
                    timeout=self.TIMEOUT
                )
                
                # Close connection
                writer.close()
                await writer.wait_closed()
                
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
        """Test multiple MTProto proxies."""
        working_proxies = []
        batch_size = 100
        
        for i in range(0, len(proxies), batch_size):
            batch = proxies[i:i + batch_size]
            
            async def test_with_callback(proxy: Dict) -> Optional[Dict]:
                # Use simple test for speed
                is_working, response_time = await self.test_proxy_simple(proxy)
                
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
            
            if i + batch_size < len(proxies):
                await asyncio.sleep(0.2)
        
        return working_proxies
    
    def test_sync(self, proxies: List[Dict], callback=None) -> List[Dict]:
        """Synchronous wrapper."""
        return asyncio.run(self.test_multiple(proxies, callback))
