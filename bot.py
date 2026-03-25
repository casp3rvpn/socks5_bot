"""
Telegram bot for SOCKS5 proxy distribution.
"""
import asyncio
from typing import Optional
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from manager import ProxyManager


class ProxyBot:
    """Telegram bot that provides working SOCKS5 proxies."""
    
    def __init__(
        self,
        token: str,
        proxy_manager: ProxyManager,
        allowed_users: Optional[list] = None
    ):
        self.token = token
        self.manager = proxy_manager
        self.allowed_users = allowed_users  # None = public
        
        self.bot = Bot(token=token)
        self.dp = Dispatcher()
        
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Register bot command handlers."""
        
        @self.dp.message(Command("start"))
        async def cmd_start(message: types.Message):
            """Handle /start command."""
            if not self._is_allowed(message.from_user.id):
                return
            
            await message.answer(
                "👋 <b>Welcome to SOCKS5 Proxy Bot!</b>\n\n"
                "I provide working SOCKS5 proxies with the lowest latency.\n\n"
                "Commands:\n"
                "📋 /proxies - Get 5 best proxies\n"
                "🔄 /refresh - Force update proxy list\n"
                "📊 /stats - Show proxy statistics\n"
                "❓ /help - Help information",
                parse_mode="HTML"
            )
        
        @self.dp.message(Command("proxies"))
        async def cmd_proxies(message: types.Message):
            """Handle /proxies command - return best proxies."""
            if not self._is_allowed(message.from_user.id):
                await message.answer("⛔ Access denied.")
                return
            
            if self.manager.is_updating:
                await message.answer("⏳ Currently updating proxies, please wait...")
                return
            
            if not self.manager.working_proxies:
                await message.answer(
                    "⚠️ No working proxies available yet.\n"
                    "Use /refresh to force an update."
                )
                return
            
            # Create inline keyboard with proxy buttons
            best = self.manager.get_best_proxies(5)
            keyboard = self._create_proxy_keyboard(best)
            
            await message.answer(
                self.manager.format_proxies_for_telegram(5),
                parse_mode="HTML",
                reply_markup=keyboard
            )
        
        @self.dp.message(Command("refresh"))
        async def cmd_refresh(message: types.Message):
            """Handle /refresh command - force update."""
            if not self._is_allowed(message.from_user.id):
                await message.answer("⛔ Access denied.")
                return
            
            status_msg = await message.answer("🔄 Updating proxy list...")
            
            count = await self.manager.update()
            
            await status_msg.edit_text(
                f"✅ Update complete!\n"
                f"Found <b>{count}</b> working proxies.\n"
                f"Use /proxies to get the list."
            )
        
        @self.dp.message(Command("stats"))
        async def cmd_stats(message: types.Message):
            """Handle /stats command."""
            if not self._is_allowed(message.from_user.id):
                await message.answer("⛔ Access denied.")
                return
            
            stats = self.manager.get_stats()
            
            await message.answer(
                f"📊 <b>Proxy Statistics</b>\n\n"
                f"📦 Working proxies: <b>{stats['total_working']}</b>\n"
                f"⏱ Last update: <b>{stats['last_update_str']}</b>\n"
                f"🔄 Update interval: <b>{stats['update_interval_minutes']} min</b>\n"
                f"⚡ Currently updating: <b>{'Yes' if stats['is_updating'] else 'No'}</b>",
                parse_mode="HTML"
            )
        
        @self.dp.message(Command("help"))
        async def cmd_help(message: types.Message):
            """Handle /help command."""
            if not self._is_allowed(message.from_user.id):
                await message.answer("⛔ Access denied.")
                return
            
            await message.answer(
                "❓ <b>Help</b>\n\n"
                "This bot provides working SOCKS5 proxies for Telegram.\n\n"
                "<b>How to use:</b>\n"
                "1. Use /proxies to get 5 best proxies\n"
                "2. Click 'Add to Telegram' button to auto-configure\n"
                "3. Or manually copy proxy details\n\n"
                "<b>Proxy format:</b>\n"
                "<code>socks5://ip:port</code>\n\n"
                "Proxies are automatically updated every 10 minutes.\n"
                "Only working proxies with lowest latency are provided.",
                parse_mode="HTML"
            )
        
        @self.dp.message(Command("raw"))
        async def cmd_raw(message: types.Message):
            """Handle /raw command - return raw proxy list."""
            if not self._is_allowed(message.from_user.id):
                await message.answer("⛔ Access denied.")
                return
            
            best = self.manager.get_best_proxies(10)
            
            if not best:
                await message.answer("No proxies available.")
                return
            
            raw_list = "\n".join([
                f"{p['ip']}:{p['port']} - {p.get('response_time', 0)}ms"
                for p in best
            ])
            
            await message.answer(
                f"<b>Raw proxy list:</b>\n\n"
                f"<code>{raw_list}</code>",
                parse_mode="HTML"
            )
    
    def _is_allowed(self, user_id: int) -> bool:
        """Check if user is allowed to use the bot."""
        if self.allowed_users is None:
            return True
        return user_id in self.allowed_users
    
    def _create_proxy_keyboard(self, proxies: list) -> InlineKeyboardMarkup:
        """Create inline keyboard with proxy buttons."""
        buttons = []
        
        for proxy in proxies:
            proxy_url = self.manager.format_for_telegram(proxy)
            tg_link = f"tg://proxy?url={proxy_url}"
            
            buttons.append([InlineKeyboardButton(
                text=f"⚡ {proxy.get('response_time', 0)}ms - {proxy['ip']}:{proxy['port']}",
                url=tg_link
            )])
        
        buttons.append([InlineKeyboardButton(
            text="🔄 Refresh",
            callback_data="refresh"
        )])
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    async def start_polling(self):
        """Start bot polling."""
        await self.dp.start_polling(self.bot)
    
    async def stop(self):
        """Stop the bot."""
        await self.bot.close()


async def run_bot(token: str, manager: ProxyManager, allowed_users: Optional[list] = None):
    """Run the proxy bot."""
    bot = ProxyBot(token, manager, allowed_users)
    
    try:
        await bot.start_polling()
    except KeyboardInterrupt:
        await bot.stop()
