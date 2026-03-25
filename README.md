# Proxy Telegram Bot (SOCKS5 + MTProto)

Telegram bot that scrapes public SOCKS5 and MTProto proxy lists, tests them for connectivity, determines their country, and provides the best working proxies to users.

## Features

- 🔄 **Automatic Updates**: Scrapes and tests proxies every 10 minutes
- ⚡ **Latency Testing**: Returns proxies with the lowest response time
- 🌍 **Country Detection**: Shows country flag for each proxy (GeoIP lookup)
- 📋 **SOCKS5 Support**: Manual configuration with host/port
- ⚡ **MTProto Support**: One-click connect via Telegram proxy links
- 💾 **Caching**: Stores working proxies for quick access
- 🔒 **Access Control**: Optional user whitelist

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create Bot Token

1. Open Telegram and find [@BotFather](https://t.me/BotFather)
2. Send `/newbot` command
3. Follow instructions to create your bot
4. Copy the API token

### 3. Configure

```bash
cp .env.example .env
```

Edit `.env` and add your bot token:

```
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

Optional: Restrict bot to specific users:
```
ALLOWED_USERS=123456789,987654321
```

### 4. Run

**Option A: Manual run**

```bash
python main.py
```

**Option B: Install as systemd service (Ubuntu/Debian)**

```bash
# Install as system service
sudo ./install_service.sh

# Edit configuration
sudo nano /opt/socks5-bot/.env

# Restart service
sudo systemctl restart socks5-bot

# View logs
sudo journalctl -u socks5-bot -f
```

**Option C: Using screen/tmux**

```bash
screen -S socks5-bot
python main.py
# Press Ctrl+A, then D to detach
```

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and bot info |
| `/proxies` | Get 5 best SOCKS5 proxies with country flags |
| `/mtproto` | Get 5 best MTProto proxies with country flags |
| `/refresh` | Force update proxy list |
| `/stats` | Show proxy statistics |
| `/help` | Help information |
| `/raw` | Get raw SOCKS5 proxy list (10 proxies) |

## SOCKS5 Proxy Output Format

```
🔥 Best SOCKS5 Proxies (lowest latency):

⏱ Updated: 2024-01-15 10:30:00

How to configure:
Settings > Advanced > Connection type > Use custom proxy > SOCKS5

1. 🇩🇪 150ms
   Host: 185.162.228.253
   Port: 4145
   Country: DE

2. 🇺🇸 200ms
   Host: 51.158.108.135
   Port: 59154
   Country: US

💡 Click on any proxy button to see details.
📋 Copy host and port manually to Telegram settings.
```

## MTProto Proxy Output Format

```
⚡ Best MTProto Proxies (lowest latency):

⏱ Updated: 2024-01-15 10:30:00

Click on 'Connect' button to auto-add to Telegram

1. 🇳🇱 120ms
   📲 Connect
   Server: proxy.example.com
   Port: 443
   Country: NL

2. 🇩🇪 180ms
   📲 Connect
   Server: mtproto.example.org
   Port: 8443
   Country: DE

💡 Click 'Connect' to automatically add to Telegram.
```

## Project Structure

```
.
├── main.py              # Entry point
├── bot.py               # Telegram bot handlers
├── manager.py           # Proxy management and scheduling
├── tester.py            # SOCKS5 proxy testing
├── scraper.py           # SOCKS5 proxy scraping
├── mtproto_tester.py    # MTProto proxy testing
├── mtproto_scraper.py   # MTProto proxy scraping
├── geoip.py             # Country detection (GeoIP)
├── requirements.txt     # Python dependencies
├── .env.example         # Configuration template
└── README.md            # This file
```

## Service Management (Ubuntu)

If installed as a systemd service:

```bash
# Check status
sudo systemctl status socks5-bot

# View logs
sudo journalctl -u socks5-bot -f
sudo tail -f /var/log/socks5-bot/bot.log

# Stop service
sudo systemctl stop socks5-bot

# Start service
sudo systemctl start socks5-bot

# Restart service
sudo systemctl restart socks5-bot

# Disable service
sudo systemctl disable socks5-bot

# Uninstall completely
sudo ./uninstall_service.sh
```

## Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | - | Bot token from @BotFather |
| `ALLOWED_USERS` | - | Comma-separated user IDs (public if empty) |
| `UPDATE_INTERVAL` | 10 | Minutes between proxy updates |
| `MAX_PROXIES` | 100 | Maximum proxies to keep (per type) |
| `MAX_CONCURRENT_TESTS` | 50 | Concurrent proxy tests |
| `CACHE_FILE` | proxies_cache.json | Cache file path |

## Proxy Sources

### SOCKS5 Sources
- proxy-list.download
- GitHub: ShiftyTR, monosans, mmpx12, proxifly, HyperBeast, clarketm, etc.
- spys.me
- socks-proxy.net

### MTProto Sources
- GitHub MTProto proxy lists
- Telegram proxy channels

## How It Works

1. **Scraping**: Bot fetches proxies from multiple public sources
2. **Testing**: Each proxy is tested for connectivity and response time
3. **GeoIP Lookup**: Country is determined for each working proxy
4. **Sorting**: Proxies are sorted by response time (lowest first)
5. **Caching**: Results are saved to JSON cache file
6. **Serving**: Users can request best proxies via bot commands

## Notes

- SOCKS5 proxies require manual configuration in Telegram
- MTProto proxies support one-click connection via `https://t.me/proxy?...` links
- Country flags are determined via GeoIP lookup (may add slight delay)
- Proxies are tested every 10 minutes automatically
- Only working proxies with lowest latency are provided
- Cache persists between bot restarts

## License

MIT
