import asyncio
import hmac
import json
import logging
import os
import re
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

import websockets
from telegram import Update, Message
from telegram.ext import Application, MessageHandler, CommandHandler, filters

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_API_KEY = os.environ["TELEGRAM_API_KEY"]
HARDWAVE_API_KEY = os.environ["HARDWAVE_API_KEY"]
ALLOWED_CHAT_ID = -1002405000000
ADMIN_IDS = {818630945, 1529429740}
WEBSOCKET_PORT = 8765

DISPLAY_TEXT_PATTERN = re.compile(r"^[a-zA-Z0-9\-_ ]{5,}$")


@dataclass
class BotState:
    enabled: bool = True
    current_message: dict | None = None
    ws_connection: websockets.WebSocketServerProtocol | None = None
    ws_lock: asyncio.Lock = None

    def __post_init__(self):
        self.ws_lock = asyncio.Lock()


state = BotState()


def is_allowed(msg: Message) -> bool:
    return (
        msg is not None
        and msg.chat_id == ALLOWED_CHAT_ID
        and msg.from_user.username
        and state.enabled
    )


async def react(msg: Message, emoji: str = "👍") -> None:
    try:
        await msg.set_reaction(emoji)
    except Exception as e:
        logger.warning("Failed to set reaction: %s", e)


async def send_ws(data: dict) -> None:
    async with state.ws_lock:
        if state.ws_connection is None:
            return
        try:
            await state.ws_connection.send(json.dumps(data))
            key = "message" if "message" in data else "command"
            logger.info("Sent %s to WebSocket: %s", key, data[key]["type"])
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed, clearing")
            state.ws_connection = None


async def handle_on(update: Update, _) -> None:
    msg = update.message
    if msg.from_user.id not in ADMIN_IDS or msg.forward_date:
        return
    state.enabled = True
    logger.info("Bot enabled by admin %s", msg.from_user.id)
    await react(msg)


async def handle_off(update: Update, _) -> None:
    msg = update.message
    if msg.from_user.id not in ADMIN_IDS or msg.forward_date:
        return
    state.enabled = False
    logger.info("Bot disabled by admin %s", msg.from_user.id)
    state.current_message = {"message": {"url": None, "type": "empty"}}
    await send_ws(state.current_message)
    await react(msg)


async def handle_display(update: Update, _) -> None:
    msg = update.message
    if not is_allowed(msg):
        return

    text = (msg.text or "")[9:]  # strip "/display "
    if not DISPLAY_TEXT_PATTERN.match(text):
        logger.info("Invalid display text from %s: %s", msg.from_user.first_name, text)
        await react(msg, "👎")
        return

    logger.info("Display command from %s: %s", msg.from_user.first_name, text)
    await send_ws({"command": {"type": "display", "text": text}})
    await react(msg)


async def handle_random(update: Update, _) -> None:
    msg = update.message
    if not is_allowed(msg):
        return
    logger.info("Random command from %s", msg.from_user.first_name)
    await send_ws({"command": {"type": "random"}})
    await react(msg)


async def handle_media(update: Update, context) -> None:
    msg = update.message
    if not is_allowed(msg) or msg.has_media_spoiler:
        return

    file_id, media_type = None, None
    if msg.photo:
        file_id, media_type = msg.photo[-1].file_id, "photo"
    elif msg.animation:
        file_id, media_type = msg.animation.file_id, "video"
    elif msg.video:
        file_id, media_type = msg.video.file_id, "video"
    elif msg.video_note:
        file_id, media_type = msg.video_note.file_id, "video"

    if not file_id:
        return

    logger.info("Detected %s from %s", media_type.upper(), msg.from_user.first_name)
    file = await context.bot.get_file(file_id)
    file_url = f"https://api.telegram.org/file/bot{TELEGRAM_API_KEY}/{file.file_path}"

    state.current_message = {"message": {"url": file_url, "type": media_type}}
    await send_ws(state.current_message)
    await react(msg)


async def websocket_handler(websocket: websockets.WebSocketServerProtocol) -> None:
    path = websocket.request.path if hasattr(websocket, "request") else websocket.path
    params = parse_qs(urlparse(path).query)
    provided_key = params.get("api_key", [""])[0]

    if not hmac.compare_digest(provided_key, HARDWAVE_API_KEY):
        logger.warning("WebSocket connection rejected: invalid API key")
        await websocket.close(1008, "Invalid API key")
        return

    async with state.ws_lock:
        if state.ws_connection is not None:
            logger.info("Dropping old WebSocket connection")
            try:
                await state.ws_connection.close(1000, "Replaced by new connection")
            except Exception:
                pass
        state.ws_connection = websocket

    logger.info("New WebSocket connection established")
    initial = state.current_message or {"message": {"url": None, "type": "empty"}}
    await websocket.send(json.dumps(initial))

    try:
        async for _ in websocket:
            pass
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        async with state.ws_lock:
            if state.ws_connection is websocket:
                state.ws_connection = None
                logger.info("WebSocket connection closed")


async def main() -> None:
    application = Application.builder().token(TELEGRAM_API_KEY).build()

    application.add_handler(CommandHandler("on", handle_on))
    application.add_handler(CommandHandler("off", handle_off))
    application.add_handler(CommandHandler("display", handle_display))
    application.add_handler(CommandHandler("random", handle_random))
    application.add_handler(
        MessageHandler(
            filters.PHOTO | filters.VIDEO | filters.ANIMATION | filters.VIDEO_NOTE,
            handle_media,
        )
    )

    ws_server = await websockets.serve(websocket_handler, "0.0.0.0", WEBSOCKET_PORT)
    logger.info("WebSocket server started on port %s", WEBSOCKET_PORT)

    async with application:
        await application.start()
        await application.updater.start_polling(drop_pending_updates=True)
        logger.info("Telegram bot started polling")

        try:
            await asyncio.Future()
        except asyncio.CancelledError:
            pass
        finally:
            await application.updater.stop()
            await application.stop()
            ws_server.close()
            await ws_server.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())
