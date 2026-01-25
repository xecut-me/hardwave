# HardWave - Telegram Media Display

Disclaimer: code is AI generated, without deep review, just kinda works. This is not a big deal as this is client-only, isolated bot on separate domain.

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

```bash
ssh -L 9222:localhost:9222 hardwave
```

chrome://inspect/#devices

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
| `require_username` | No | Only display media from users with a Telegram username | `?require_username=1` or `?require_username=true` |

## Features

- Displays photos, GIFs, videos, and video notes sent directly to the bot
- Shows sender name and username in the top left
- Auto-plays videos and GIFs (muted, looped)
- Long-polling for real-time updates
- Ignores spoilered media (messages with `has_media_spoiler`)
- All received updates are logged to browser console as JSON (for debugging)
- Press **Enter** to toggle aspect ratio preservation on/off
- Key display overlay: shows pressed keys on screen with animated fade-out

## WebHID Keyboard Integration

The page includes WebHID support for a custom keyboard device (Adafruit, VID: 0x239A, PID: 0x80B4). Features:

- **Time sync**: Automatically syncs time to the device on page load (Europe/Belgrade timezone)
- **`/display <text>` command**: Send this command in the Telegram chat to display running text on the HID device. Text must be at least 5 characters and contain only `a-zA-Z0-9-_` and spaces.
- **`/random` command**: Sends 100 random raw packages to the HID device for testing.

## Admin Commands

- **`/killswitch`**: Stops the bot and displays a message to restart via SSH. Only works for authorized sender IDs (not forwarded messages).

## Examples

```
# Basic usage (both api_key and chat_id required)
index.html?api_key=123456789:ABCdefGHIjklMNOpqrsTUVwxyz&chat_id=-1001234567890

# With preserved aspect ratio
index.html?api_key=123456789:ABCdefGHIjklMNOpqrsTUVwxyz&chat_id=-1001234567890&respect_aspect_ratio=1

# Only show media from users with usernames
index.html?api_key=123456789:ABCdefGHIjklMNOpqrsTUVwxyz&chat_id=-1001234567890&require_username=1
```
