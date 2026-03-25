#!/usr/bin/env python3
"""
SOCKS5 Proxy Telegram Bot - Main Entry Point

This bot scrapes public SOCKS5 proxy lists, tests them for connectivity,
and provides the best working proxies to Telegram users.

Usage:
    1. Copy .env.example to .env
    2. Add your Telegram bot token to .env
    3. Run: python main.py
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from manager import ProxyManager
from bot import ProxyBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config() -> dict:
    """Load configuration from environment."""
    load_dotenv()
    
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token or token == 'your_bot_token_here':
        logger.error("❌ TELEGRAM_BOT_TOKEN not set in .env file!")
        logger.error("   Copy .env.example to .env and add your bot token.")
        sys.exit(1)
    
    # Parse allowed users
    allowed_users_str = os.getenv('ALLOWED_USERS', '')
    allowed_users = None
    if allowed_users_str:
        try:
            allowed_users = [int(x.strip()) for x in allowed_users_str.split(',')]
        except ValueError:
            logger.warning("Invalid ALLOWED_USERS format, bot will be public")
    
    return {
        'token': token,
        'allowed_users': allowed_users,
        'update_interval': int(os.getenv('UPDATE_INTERVAL', '10')),
        'max_proxies': int(os.getenv('MAX_PROXIES', '100')),
        'max_concurrent_tests': int(os.getenv('MAX_CONCURRENT_TESTS', '50')),
        'cache_file': os.getenv('CACHE_FILE', 'proxies_cache.json'),
    }


async def main():
    """Main entry point."""
    logger.info("🚀 Starting SOCKS5 Proxy Bot...")
    
    # Load configuration
    config = load_config()
    
    # Create proxy manager
    manager = ProxyManager(
        cache_file=config['cache_file'],
        update_interval_minutes=config['update_interval'],
        max_proxies=config['max_proxies'],
        max_concurrent_tests=config['max_concurrent_tests']
    )
    
    # Setup update callback
    async def on_update(result):
        logger.info(f"✅ Update complete: {result['socks5']} SOCKS5, {result['mtproto']} MTProto")

    manager.set_update_callback(on_update)

    # Start the manager (begins scheduled updates)
    manager.start()
    logger.info(f"📡 Proxy manager started (updates every {config['update_interval']} min)")

    # Load cached proxies (no automatic update at startup)
    if manager.load_from_cache():
        logger.info(f"📦 Loaded {len(manager.working_proxies)} proxies from cache")
    else:
        logger.info("📭 No cached proxies found")

    # Create and start bot
    bot = ProxyBot(
        token=config['token'],
        proxy_manager=manager,
        allowed_users=config['allowed_users']
    )
    
    if config['allowed_users']:
        logger.info(f"🔒 Bot restricted to {len(config['allowed_users'])} users")
    else:
        logger.info("🌍 Bot is public")
    
    logger.info("🤖 Bot is running... Press Ctrl+C to stop")
    
    try:
        await bot.start_polling()
    except KeyboardInterrupt:
        logger.info("\n👋 Shutting down...")
    finally:
        manager.stop()
        await bot.stop()
        logger.info("✅ Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
