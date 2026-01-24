# Hardwave - Telegram Media Display

Disclaimer: this shit was vibe coded and I do not reviewed this code. This is not a big deal as this is client-only, isolated bot on separate domain.

A simple web page that displays photos and videos sent to a Telegram bot in real-time.

## Deploy (admin only)

Update https://hardwave.tgr.rs/

```
ssh hardwave
vim /etc/init.d/kiosk
rc-service kiosk restart
```

## Setup

1. Create a Telegram bot via [@BotFather](https://t.me/BotFather) and get your API key
2. Open the page with your API key: `index.html?api_key=YOUR_BOT_TOKEN`

The API key is stored in localStorage, so you only need to provide it once.

## URL Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `api_key` | Telegram bot token (required on first visit) | `?api_key=123456:ABC...` |
| `chat_id` | Only show media from this chat ID | `?chat_id=123` |
| `json` | Show raw JSON instead of media | `?json=1` or `?json=true` |
| `aspect_ratio` | Preserve aspect ratio (off by default, stretches to fill) | `?aspect_ratio=1` or `?aspect_ratio=true` |

## Features

- Displays photos and videos sent to the bot
- Shows sender name and username in the top left
- Auto-plays videos (muted, looped)
- Persists last received media across page reloads
- Long-polling for real-time updates

## Examples

```
# Basic usage
index.html?api_key=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# Filter by specific chat
index.html?chat_id=123

# Preserve aspect ratio
index.html?aspect_ratio=1

# Debug mode (show JSON)
index.html?json=1
```
