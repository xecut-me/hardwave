# Hardwave - Telegram Media Display

Disclaimer: this shit was vibe coded and I do not reviewed this code. This is not a big deal as this is client-only, isolated bot on separate domain.

A simple web page that displays photos, videos and GIFs sent to a Telegram bot in real-time. Intentionally distorts images to fit whole screen (feature can be disabled).

## Deploy (admin only)

Update https://hardwave.tgr.rs/

```
ssh hardwave
vim /etc/init.d/kiosk
rc-service kiosk restart
```

## Debug

```
ssh hardwave
su kiosk
rm screenshot.png
DISPLAY=:0 scrot ~/screenshot.png
scp hardwave:/home/kiosk/screenshot.png .
```

## Setup

1. Create a Telegram bot via [@BotFather](https://t.me/BotFather) and get your API key
2. Get the chat ID of the chat you want to display media from
3. Open the page with required parameters: `index.html?api_key=YOUR_BOT_TOKEN&chat_id=YOUR_CHAT_ID`

## URL Parameters

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `api_key` | Yes | Telegram bot token | `?api_key=123456:ABC...` |
| `chat_id` | Yes | Only show media from this chat ID | `?chat_id=-1001234567890` |
| `respect_aspect_ratio` | No | Preserve aspect ratio (off by default, stretches to fill) | `?respect_aspect_ratio=1` or `?respect_aspect_ratio=true` |

## Features

- Displays photos, GIFs, and videos sent directly to the bot
- Shows sender name and username in the top left
- Auto-plays videos and GIFs (muted, looped)
- Long-polling for real-time updates
- All received updates are logged to browser console as JSON (for debugging)

## Examples

```
# Basic usage (both api_key and chat_id required)
index.html?api_key=123456789:ABCdefGHIjklMNOpqrsTUVwxyz&chat_id=-1001234567890

# With preserved aspect ratio
index.html?api_key=123456789:ABCdefGHIjklMNOpqrsTUVwxyz&chat_id=-1001234567890&respect_aspect_ratio=1
```
