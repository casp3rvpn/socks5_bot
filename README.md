# SOCKS5 Proxy Telegram Bot

Telegram bot that scrapes public SOCKS5 proxy lists, tests them for connectivity, and provides the best working proxies to users.

## Features

- 🔄 **Automatic Updates**: Scrapes and tests proxies every 10 minutes
- ⚡ **Latency Testing**: Returns proxies with the lowest response time
- 📲 **One-Click Setup**: Proxies formatted for automatic Telegram client configuration
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

```bash
python main.py
```

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and bot info |
| `/proxies` | Get 5 best working proxies |
| `/refresh` | Force update proxy list |
| `/stats` | Show proxy statistics |
| `/help` | Help information |
| `/raw` | Get raw proxy list (10 proxies) |

## Proxy Output Format

The bot returns proxies in a format suitable for automatic Telegram client setup:

```
🔥 Best SOCKS5 Proxies (lowest latency):

⏱ Updated: 2024-01-15 10:30:00

1. ⚡ 150ms - 185.162.228.253:4145
   📲 Add to Telegram

2. ⚡ 200ms - 51.158.108.135:59154
   📲 Add to Telegram

...
```

Clicking "Add to Telegram" opens a deep link (`tg://proxy?url=socks5://ip:port`) that automatically configures the proxy in the Telegram client.

## Project Structure

```
.
├── main.py          # Entry point
├── bot.py           # Telegram bot handlers
├── manager.py       # Proxy management and scheduling
├── tester.py        # Proxy connectivity testing
├── scraper.py       # Proxy list scraping
├── requirements.txt # Python dependencies
├── .env.example     # Configuration template
└── README.md        # This file
```

## Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | - | Bot token from @BotFather |
| `ALLOWED_USERS` | - | Comma-separated user IDs (public if empty) |
| `UPDATE_INTERVAL` | 10 | Minutes between proxy updates |
| `MAX_PROXIES` | 100 | Maximum proxies to keep |
| `MAX_CONCURRENT_TESTS` | 50 | Concurrent proxy tests |
| `CACHE_FILE` | proxies_cache.json | Cache file path |

## Notes

- The bot scrapes multiple public proxy sources
- Only working SOCKS5 proxies are returned
- Proxies are sorted by response time (lowest first)
- Cache is updated after each successful scrape/test cycle

## License

MIT
