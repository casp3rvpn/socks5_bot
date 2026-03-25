"""
Proxy manager module - manages proxy list with scheduled updates.
Supports both SOCKS5 and MTProto proxies.
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
from mtproto_scraper import MTProtoScraper
from mtproto_tester import MTProtoTester
from geoip import GeoIP


class ProxyManager:
    """
    Manages SOCKS5 and MTProto proxy lists with automatic scraping and testing.
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
        
        # SOCKS5
        self.scraper = ProxyScraper()
        self.tester = ProxyTester(max_concurrent=max_concurrent_tests)
        
        # MTProto
        self.mtproto_scraper = MTProtoScraper()
        self.mtproto_tester = MTProtoTester(max_concurrent=max_concurrent_tests)
        
        # GeoIP
        self.geoip = GeoIP(max_concurrent=20)
        
        self.scheduler = AsyncIOScheduler()
        
        self._working_proxies: List[Dict] = []
        self._working_mtproto: List[Dict] = []
        self._last_update: float = 0
        self._is_updating: bool = False
        self._update_callback: Optional[Callable] = None
    
    @property
    def working_proxies(self) -> List[Dict]:
        """Get current list of working SOCKS5 proxies."""
        return self._working_proxies.copy()
    
    @property
    def working_mtproto(self) -> List[Dict]:
        """Get current list of working MTProto proxies."""
        return self._working_mtproto.copy()
    
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
        """Get best SOCKS5 proxies sorted by response time."""
        sorted_proxies = sorted(
            self._working_proxies,
            key=lambda p: p.get('response_time', float('inf'))
        )
        return sorted_proxies[:count]
    
    def get_best_mtproto(self, count: int = 5) -> List[Dict]:
        """Get best MTProto proxies sorted by response time."""
        sorted_proxies = sorted(
            self._working_mtproto,
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
            
            self._working_proxies = data.get('socks5_proxies', [])
            self._working_mtproto = data.get('mtproto_proxies', [])
            self._last_update = data.get('last_update', 0)
            
            return True
        except Exception:
            return False
    
    def save_to_cache(self):
        """Save proxies to cache file."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump({
                    'socks5_proxies': self._working_proxies,
                    'mtproto_proxies': self._working_mtproto,
                    'last_update': self._last_update
                }, f, indent=2)
        except Exception:
            pass
    
    async def update(self, debug: bool = False) -> dict:
        """Run a full update cycle: scrape and test both SOCKS5 and MTProto proxies."""
        if self._is_updating:
            return {'socks5': len(self._working_proxies), 'mtproto': len(self._working_mtproto)}
        
        self._is_updating = True
        start_time = time.time()
        
        try:
            # === SOCKS5 Proxies ===
            if debug:
                print("🔍 Scraping SOCKS5 proxies...")
            socks5_scraped = await self.scraper.scrape_all(debug=debug)
            
            socks5_working = []
            if socks5_scraped:
                if debug:
                    print(f"📦 Found {len(socks5_scraped)} SOCKS5 proxies, testing...")
                
                # Test SOCKS5 proxies
                tested = 0
                async def on_test_socks5(proxy, is_working, response_time):
                    nonlocal tested
                    tested += 1
                    if is_working:
                        if debug and tested <= 10:
                            print(f"  ✓ {proxy['ip']}:{proxy['port']} - {response_time}ms")
                    if debug and tested % 500 == 0:
                        print(f"  Progress: {tested}/{len(socks5_scraped)} tested")
                
                socks5_working = await self.tester.test_multiple(socks5_scraped, callback=on_test_socks5)
                
                if debug:
                    print(f"✅ SOCKS5: {len(socks5_working)} working")
            
            # === MTProto Proxies ===
            if debug:
                print("\n🔍 Scraping MTProto proxies...")
            mtproto_scraped = await self.mtproto_scraper.scrape_all(debug=debug)
            
            mtproto_working = []
            if mtproto_scraped:
                if debug:
                    print(f"📦 Found {len(mtproto_scraped)} MTProto proxies, testing...")
                
                # Test MTProto proxies
                async def on_test_mtproto(proxy, is_working, response_time):
                    if is_working and debug:
                        print(f"  ✓ {proxy['server']}:{proxy['port']} - {response_time}ms")
                
                mtproto_working = await self.mtproto_tester.test_multiple(mtproto_scraped, callback=on_test_mtproto)
                
                if debug:
                    print(f"✅ MTProto: {len(mtproto_working)} working")
            
            # === GeoIP Lookup ===
            if debug:
                print("\n🌍 Looking up countries...")
            
            # Enrich SOCKS5 proxies with country info
            if socks5_working:
                socks5_enriched = await self.geoip.lookup_multiple(socks5_working)
                self._working_proxies = sorted(
                    socks5_enriched,
                    key=lambda p: p.get('response_time', float('inf'))
                )[:self.max_proxies]
            
            # Enrich MTProto proxies with country info
            if mtproto_working:
                mtproto_enriched = await self.geoip.lookup_multiple(mtproto_working)
                self._working_mtproto = sorted(
                    mtproto_enriched,
                    key=lambda p: p.get('response_time', float('inf'))
                )[:self.max_proxies]
            
            self._last_update = time.time()
            self.save_to_cache()
            
            elapsed = time.time() - start_time
            if debug:
                print(f"\n✅ Done in {elapsed:.1f}s")
                print(f"   SOCKS5: {len(self._working_proxies)}")
                print(f"   MTProto: {len(self._working_mtproto)}")
            
            if self._update_callback:
                await self._update_callback({
                    'socks5': len(self._working_proxies),
                    'mtproto': len(self._working_mtproto)
                })
            
            return {
                'socks5': len(self._working_proxies),
                'mtproto': len(self._working_mtproto)
            }
        
        finally:
            self._is_updating = False
    
    def start(self):
        """Start the scheduler."""
        # Schedule regular updates
        self.scheduler.add_job(
            self.update,
            trigger=IntervalTrigger(minutes=self.update_interval),
            id='proxy_update',
            replace_existing=True
        )

        self.scheduler.start()
    
    def stop(self):
        """Stop the scheduler."""
        self.scheduler.shutdown()
    
    def get_stats(self) -> Dict:
        """Get manager statistics."""
        return {
            'total_socks5': len(self._working_proxies),
            'total_mtproto': len(self._working_mtproto),
            'last_update': self._last_update,
            'last_update_str': time.strftime(
                '%Y-%m-%d %H:%M:%S',
                time.localtime(self._last_update)
            ) if self._last_update else 'Never',
            'is_updating': self._is_updating,
            'update_interval_minutes': self.update_interval
        }

    def format_proxies_for_telegram(self, count: int = 5) -> str:
        """Format best SOCKS5 proxies for Telegram with country flags."""
        best = self.get_best_proxies(count)

        if not best:
            return "❌ No working SOCKS5 proxies available."

        lines = [
            "🔥 <b>Best SOCKS5 Proxies</b> (lowest latency):\n",
            f"⏱ Updated: {self.get_stats()['last_update_str']}\n\n",
            "<b>How to configure:</b>\n",
            "Settings > Advanced > Connection type > Use custom proxy > SOCKS5\n\n"
        ]

        for i, proxy in enumerate(best, 1):
            response_time = proxy.get('response_time', 0)
            flag = proxy.get('flag', '🌐')
            country = proxy.get('country', 'Unknown')
            
            lines.append(
                f"{i}. {flag} <b>{response_time}ms</b>\n"
                f"   <code>Host: {proxy['ip']}</code>\n"
                f"   <code>Port: {proxy['port']}</code>\n"
                f"   <code>Country: {country}</code>\n"
            )

        lines.append(
            "\n💡 <i>Click on any proxy button to see details.</i>\n"
            "📋 Copy host and port manually to Telegram settings."
        )

        return "".join(lines)

    def format_mtproto_for_telegram(self, count: int = 5) -> str:
        """Format best MTProto proxies for Telegram with country flags."""
        best = self.get_best_mtproto(count)

        if not best:
            return "❌ No working MTProto proxies available."

        import urllib.parse
        
        lines = [
            "⚡ <b>Best MTProto Proxies</b> (lowest latency):\n",
            f"⏱ Updated: {self.get_stats()['last_update_str']}\n\n",
            "<b>How to configure:</b>\n",
            "Click on 'Connect' button to auto-add to Telegram\n\n"
        ]

        for i, proxy in enumerate(best, 1):
            response_time = proxy.get('response_time', 0)
            flag = proxy.get('flag', '🌐')
            country = proxy.get('country', 'Unknown')
            
            # Create MTProto link
            secret_encoded = urllib.parse.quote(proxy['secret'], safe='')
            tg_link = f"https://t.me/proxy?server={proxy['server']}&port={proxy['port']}&secret={secret_encoded}"
            
            lines.append(
                f"{i}. {flag} <b>{response_time}ms</b>\n"
                f"   <a href='{tg_link}'>📲 Connect</a>\n"
                f"   <code>Server: {proxy['server']}</code>\n"
                f"   <code>Port: {proxy['port']}</code>\n"
                f"   <code>Country: {country}</code>\n\n"
            )

        lines.append(
            "💡 <i>Click 'Connect' to automatically add to Telegram.</i>"
        )

        return "".join(lines)


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
