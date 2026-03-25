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
                "👋 <b>Welcome to Proxy Bot!</b>\n\n"
                "I provide working SOCKS5 and MTProto proxies with lowest latency.\n\n"
                "Commands:\n"
                "📋 /proxies - Get 5 best SOCKS5 proxies\n"
                "⚡ /mtproto - Get 5 best MTProto proxies\n"
                "🔄 /refresh - Force update proxy list\n"
                "📊 /stats - Show statistics\n"
                "❓ /help - Help information",
                parse_mode="HTML"
            )
        
        @self.dp.message(Command("proxies"))
        async def cmd_proxies(message: types.Message):
            """Handle /proxies command - return best SOCKS5 proxies."""
            if not self._is_allowed(message.from_user.id):
                await message.answer("⛔ Access denied.")
                return

            if self.manager.is_updating:
                await message.answer("⏳ Currently updating proxies, please wait...")
                return

            if not self.manager.working_proxies:
                await message.answer(
                    "⚠️ No working SOCKS5 proxies available yet.\n"
                    "Use /refresh to force an update."
                )
                return

            # Create inline keyboard with proxy buttons
            best = self.manager.get_best_proxies(5)
            keyboard = self._create_socks5_keyboard(best)

            await message.answer(
                self.manager.format_proxies_for_telegram(5),
                parse_mode="HTML",
                reply_markup=keyboard
            )

        @self.dp.message(Command("mtproto"))
        async def cmd_mtproto(message: types.Message):
            """Handle /mtproto command - return best MTProto proxies."""
            if not self._is_allowed(message.from_user.id):
                await message.answer("⛔ Access denied.")
                return

            if self.manager.is_updating:
                await message.answer("⏳ Currently updating proxies, please wait...")
                return

            if not self.manager.working_mtproto:
                await message.answer(
                    "⚠️ No working MTProto proxies available yet.\n"
                    "Use /refresh to force an update."
                )
                return

            # Create inline keyboard with MTProto buttons
            best = self.manager.get_best_mtproto(5)
            keyboard = self._create_mtproto_keyboard(best)

            await message.answer(
                self.manager.format_mtproto_for_telegram(5),
                parse_mode="HTML",
                reply_markup=keyboard,
                disable_web_page_preview=True
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
                f"📦 SOCKS5 proxies: <b>{stats['total_socks5']}</b>\n"
                f"⚡ MTProto proxies: <b>{stats['total_mtproto']}</b>\n"
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
                "This bot provides working SOCKS5 and MTProto proxies.\n\n"
                "<b>Commands:</b>\n"
                "📋 /proxies - Get 5 best SOCKS5 proxies\n"
                "⚡ /mtproto - Get 5 best MTProto proxies\n"
                "🔄 /refresh - Force update proxy list\n"
                "📊 /stats - Show statistics\n"
                "❓ /help - Help information\n\n"
                "<b>SOCKS5 Setup:</b>\n"
                "Settings > Advanced > Connection type > SOCKS5\n"
                "Copy host and port from /proxies\n\n"
                "<b>MTProto Setup:</b>\n"
                "Click 'Connect' button in /mtproto\n"
                "Or copy server, port, secret manually\n\n"
                "Proxies update every 10 minutes automatically.",
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

        @self.dp.callback_query()
        async def handle_callback(callback: types.CallbackQuery):
            """Handle inline button callbacks."""
            if callback.data == "refresh":
                if not self._is_allowed(callback.from_user.id):
                    await callback.answer("⛔ Access denied.", show_alert=True)
                    return

                await callback.message.edit_text("🔄 Updating proxy list...")
                result = await self.manager.update()
                await callback.message.edit_text(
                    f"✅ Update complete!\n"
                    f"📦 SOCKS5: <b>{result['socks5']}</b>\n"
                    f"⚡ MTProto: <b>{result['mtproto']}</b>\n\n"
                    f"Use /proxies or /mtproto to get the list.",
                    parse_mode="HTML"
                )
            elif callback.data.startswith("socks5_"):
                # Show SOCKS5 proxy details
                parts = callback.data.replace("socks5_", "").split("_")
                if len(parts) >= 2:
                    ip = parts[0]
                    port = parts[1]
                    await callback.answer(
                        f"SOCKS5 Proxy:\n\n"
                        f"Host: {ip}\n"
                        f"Port: {port}\n\n"
                        f"Configure in Telegram:\n"
                        f"Settings > Advanced > Connection type > SOCKS5",
                        show_alert=True
                    )
    
    def _is_allowed(self, user_id: int) -> bool:
        """Check if user is allowed to use the bot."""
        if self.allowed_users is None:
            return True
        return user_id in self.allowed_users
    
    def _create_socks5_keyboard(self, proxies: list) -> InlineKeyboardMarkup:
        """Create inline keyboard with SOCKS5 proxy buttons."""
        buttons = []

        for proxy in proxies:
            flag = proxy.get('flag', '🌐')
            country = proxy.get('country', 'Unknown')
            buttons.append([InlineKeyboardButton(
                text=f"{flag} {proxy.get('response_time', 0)}ms - {proxy['ip']}:{proxy['port']}",
                callback_data=f"socks5_{proxy['ip']}_{proxy['port']}"
            )])

        buttons.append([InlineKeyboardButton(
            text="🔄 Refresh",
            callback_data="refresh"
        )])

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    def _create_mtproto_keyboard(self, proxies: list) -> InlineKeyboardMarkup:
        """Create inline keyboard with MTProto proxy buttons."""
        import urllib.parse
        buttons = []

        for proxy in proxies:
            flag = proxy.get('flag', '🌐')
            # Create MTProto link
            secret_encoded = urllib.parse.quote(proxy['secret'], safe='')
            tg_link = f"https://t.me/proxy?server={proxy['server']}&port={proxy['port']}&secret={secret_encoded}"
            
            buttons.append([InlineKeyboardButton(
                text=f"{flag} {proxy.get('response_time', 0)}ms - {proxy['server']}:{proxy['port']}",
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
