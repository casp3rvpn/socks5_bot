"""
Proxy manager module - manages proxy list with scheduled updates.
"""
import asyncio
import json
import time
from pathlib import Path
from typing import List, Dict, Optional, Callable
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from scraper import ProxyScraper
from tester import ProxyTester


class ProxyManager:
    """
    Manages SOCKS5 proxy list with automatic scraping and testing.
    Runs updates on a schedule and provides access to working proxies.
    """
    
    def __init__(
        self,
        cache_file: str = "proxies_cache.json",
        update_interval_minutes: int = 10,
        max_proxies: int = 100,
        max_concurrent_tests: int = 50
    ):
        self.cache_file = Path(cache_file)
        self.update_interval = update_interval_minutes
        self.max_proxies = max_proxies
        self.max_concurrent_tests = max_concurrent_tests
        
        self.scraper = ProxyScraper()
        self.tester = ProxyTester(max_concurrent=max_concurrent_tests)
        
        self.scheduler = AsyncIOScheduler()
        
        self._working_proxies: List[Dict] = []
        self._last_update: float = 0
        self._is_updating: bool = False
        self._update_callback: Optional[Callable] = None
    
    @property
    def working_proxies(self) -> List[Dict]:
        """Get current list of working proxies."""
        return self._working_proxies.copy()
    
    @property
    def last_update(self) -> float:
        """Get timestamp of last update."""
        return self._last_update
    
    @property
    def is_updating(self) -> bool:
        """Check if update is in progress."""
        return self._is_updating
    
    def set_update_callback(self, callback: Callable):
        """Set callback to be called after each update."""
        self._update_callback = callback
    
    def get_best_proxies(self, count: int = 5) -> List[Dict]:
        """
        Get best proxies sorted by response time.
        
        Args:
            count: Number of proxies to return
        
        Returns:
            List of best proxies with lowest response time
        """
        sorted_proxies = sorted(
            self._working_proxies,
            key=lambda p: p.get('response_time', float('inf'))
        )
        return sorted_proxies[:count]
    
    def load_from_cache(self) -> bool:
        """Load proxies from cache file."""
        if not self.cache_file.exists():
            return False
        
        try:
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
            
            self._working_proxies = data.get('proxies', [])
            self._last_update = data.get('last_update', 0)
            
            # Filter out old proxies (checked more than 30 minutes ago)
            current_time = time.time()
            max_age = 30 * 60  # 30 minutes
            
            self._working_proxies = [
                p for p in self._working_proxies
                if current_time - p.get('last_checked', 0) < max_age
            ]
            
            return True
        except Exception:
            return False
    
    def save_to_cache(self):
        """Save proxies to cache file."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump({
                    'proxies': self._working_proxies,
                    'last_update': self._last_update
                }, f, indent=2)
        except Exception:
            pass
    
    async def update(self, debug: bool = False) -> int:
        """
        Run a full update cycle: scrape and test proxies.
        
        Returns:
            Number of working proxies found
        """
        if self._is_updating:
            return len(self._working_proxies)
        
        self._is_updating = True
        
        try:
            # Scrape new proxies
            if debug:
                print("🔍 Scraping proxies...")
            scraped = await self.scraper.scrape_all(debug=debug)
            
            if debug:
                print(f"📦 Scraped {len(scraped)} proxies, testing...")
            
            if not scraped:
                # If scraping failed, try to use cached proxies
                if debug:
                    print("⚠️ No proxies scraped, using cache")
                self.load_from_cache()
                return len(self._working_proxies)
            
            # Test scraped proxies
            tested = 0
            async def on_test(proxy, is_working, response_time):
                nonlocal tested
                tested += 1
                if debug and is_working:
                    print(f"  ✓ {proxy['ip']}:{proxy['port']} - {response_time}ms")
            
            working = await self.tester.test_multiple(scraped, callback=on_test)
            
            if debug:
                print(f"✅ Tested {tested} proxies, {len(working)} working")
            
            # Keep best proxies
            if working:
                self._working_proxies = sorted(
                    working,
                    key=lambda p: p.get('response_time', float('inf'))
                )[:self.max_proxies]
            
            self._last_update = time.time()
            self.save_to_cache()
            
            if self._update_callback:
                await self._update_callback(len(self._working_proxies))
            
            return len(self._working_proxies)
        
        finally:
            self._is_updating = False
    
    def start(self):
        """Start the scheduler."""
        # Load cached proxies first
        self.load_from_cache()
        
        # Schedule regular updates
        self.scheduler.add_job(
            self.update,
            trigger=IntervalTrigger(minutes=self.update_interval),
            id='proxy_update',
            replace_existing=True
        )
        
        self.scheduler.start()
        
        # Run initial update
        asyncio.create_task(self.update())
    
    def stop(self):
        """Stop the scheduler."""
        self.scheduler.shutdown()
    
    def get_stats(self) -> Dict:
        """Get manager statistics."""
        return {
            'total_working': len(self._working_proxies),
            'last_update': self._last_update,
            'last_update_str': time.strftime(
                '%Y-%m-%d %H:%M:%S',
                time.localtime(self._last_update)
            ) if self._last_update else 'Never',
            'is_updating': self._is_updating,
            'update_interval_minutes': self.update_interval
        }
    
    def format_for_telegram(self, proxy: Dict) -> str:
        """
        Format proxy for Telegram client import.
        
        Telegram proxy format:
        socks5://ip:port or for MTProto proxy links
        
        For automatic setup, we use the format that can be 
        directly imported via tg://proxy?url=
        """
        # Standard SOCKS5 format for Telegram
        return f"socks5://{proxy['ip']}:{proxy['port']}"
    
    def format_proxies_for_telegram(self, count: int = 5) -> str:
        """
        Format best proxies for Telegram client import.
        
        Returns formatted text with proxy links.
        """
        best = self.get_best_proxies(count)
        
        if not best:
            return "❌ No working proxies available at the moment."
        
        lines = [
            "🔥 <b>Best SOCKS5 Proxies</b> (lowest latency):\n",
            f"⏱ Updated: {self.get_stats()['last_update_str']}\n"
        ]
        
        for i, proxy in enumerate(best, 1):
            response_time = proxy.get('response_time', 0)
            proxy_url = self.format_for_telegram(proxy)
            
            # Telegram proxy link format
            tg_link = f"tg://proxy?url={proxy_url}"
            
            lines.append(
                f"{i}. ⚡ <b>{response_time}ms</b> - "
                f"<code>{proxy['ip']}:{proxy['port']}</code>\n"
                f"   <a href='{tg_link}'>📲 Add to Telegram</a>\n"
            )
        
        lines.append(
            "\n💡 <i>Click 'Add to Telegram' to automatically configure "
            "the proxy in your Telegram client.</i>"
        )
        
        return "\n".join(lines)


async def demo_manager():
    """Demo function for ProxyManager."""
    manager = ProxyManager(
        cache_file="demo_cache.json",
        update_interval_minutes=10,
        max_proxies=20
    )
    
    async def on_update(count):
        print(f"Update complete: {count} working proxies found")
    
    manager.set_update_callback(on_update)
    
    print("Starting proxy update...")
    count = await manager.update()
    print(f"Found {count} working proxies")
    
    print("\nBest 5 proxies:")
    print(manager.format_proxies_for_telegram(5))


if __name__ == "__main__":
    asyncio.run(demo_manager())
