import asyncio
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import requests
from telegram import Update
from telegram.ext import Application, CommandHandler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_API_KEY = os.environ["TELEGRAM_API_KEY"]
ALLOWED_CHAT_IDS = {int(x) for x in os.environ["ALLOWED_CHAT_IDS"].split(",")}
ADMIN_ID = int(os.environ["ADMIN_ID"])
LLM_API_URL = os.environ["LLM_API_URL"]
LLM_API_KEY = os.environ["LLM_API_KEY"]
LLM_API_MODEL = os.environ.get("LLM_API_MODEL", "claude-3-5-sonnet-20241022")
URL_BASE = "https://xecut-ai-ugc.tgr.rs/"

RESULTS_DIR = Path(__file__).parent / "results"
BASE_PROMPT_PATH = Path(__file__).parent / "base_prompt.md"

# State management
ai_enabled_chats = set()  # Chats where AI is enabled
task_queue = asyncio.Queue()
processing = False


def is_allowed(update: Update) -> bool:
    msg = update.message
    if msg is None:
        return False
    if msg.chat_id not in ALLOWED_CHAT_IDS:
        logger.debug("Rejected: chat_id %s not in allowed list", msg.chat_id)
        return False
    return True


def is_admin(update: Update) -> bool:
    msg = update.message
    if msg is None or msg.from_user is None:
        return False
    return msg.from_user.id == ADMIN_ID


def is_ai_enabled(chat_id: int) -> bool:
    return chat_id in ai_enabled_chats


def _call_api(prompt: str) -> str:
    """Synchronous API call to be run in thread pool."""
    response = requests.post(
        f"{LLM_API_URL}/messages",
        headers={
            "x-api-key": LLM_API_KEY,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        json={
            "model": LLM_API_MODEL,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=300,
    )
    response.raise_for_status()
    data = response.json()
    return data["content"][0]["text"]


async def generate_html(prompt: str) -> tuple[str, str]:
    """Generate HTML and return (file_path, html_content)."""
    base_prompt = BASE_PROMPT_PATH.read_text()
    full_prompt = f"{base_prompt}\n\n# Task\n\n{prompt}"

    # Run synchronous requests call in thread pool
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        content = await loop.run_in_executor(executor, _call_api, full_prompt)

    match = re.search(r"```html\s*(.*?)\s*```", content, re.DOTALL)
    html = match.group(1) if match else content

    # Use timestamp for filename
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    RESULTS_DIR.mkdir(exist_ok=True)
    result_path = RESULTS_DIR / f"{timestamp}.html"
    result_path.write_text(html)

    return str(result_path), html


async def process_queue():
    """Process tasks from queue one at a time."""
    global processing
    while True:
        update, prompt = await task_queue.get()
        processing = True
        msg = update.message

        try:
            result_path, html = await generate_html(prompt)
            filename = Path(result_path).name
            url = f"{URL_BASE}{filename}"

            # Send URL and HTML document
            await msg.reply_text(f"ok\n{url}")
            await msg.reply_document(document=open(result_path, "rb"), filename=filename)

            logger.info("Task completed: %s", filename)
        except Exception as e:
            logger.error("Task failed: %s", e, exc_info=True)
            print(f"Error generating HTML: {e}", file=sys.stderr)
            await msg.reply_text("error generating")
        finally:
            processing = False
            task_queue.task_done()


async def handle_make(update: Update, _) -> None:
    if not is_allowed(update):
        return

    msg = update.message
    chat_id = msg.chat_id

    # Check if AI is enabled for this chat (unless admin)
    if not is_admin(update) and not is_ai_enabled(chat_id):
        return

    text = msg.text or ""
    prompt = text[6:].strip()  # strip "/make "

    if not prompt:
        await msg.reply_text("Usage: /make <prompt>")
        return

    # Add to queue
    await task_queue.put((update, prompt))
    logger.info("Task queued for chat %s: %s", chat_id, prompt)


async def handle_ai_on(update: Update, _) -> None:
    if not is_allowed(update):
        return

    msg = update.message

    # Admin only, not forwarded, in the exact chat
    if not is_admin(update):
        return
    if msg.forward_date is not None:
        return

    chat_id = msg.chat_id
    ai_enabled_chats.add(chat_id)
    await msg.reply_text("AI enabled")
    logger.info("AI enabled for chat %s", chat_id)


async def handle_ai_off(update: Update, _) -> None:
    if not is_allowed(update):
        return

    msg = update.message

    # Admin only, not forwarded, in the exact chat
    if not is_admin(update):
        return
    if msg.forward_date is not None:
        return

    chat_id = msg.chat_id
    ai_enabled_chats.discard(chat_id)
    await msg.reply_text("AI disabled")
    logger.info("AI disabled for chat %s", chat_id)


async def handle_ai_clean(update: Update, _) -> None:
    if not is_allowed(update):
        return

    msg = update.message

    # Admin only
    if not is_admin(update):
        return

    # Delete all files in results directory
    count = 0
    if RESULTS_DIR.exists():
        for file in RESULTS_DIR.glob("*.html"):
            file.unlink()
            count += 1

    await msg.reply_text(f"Cleaned {count} files")
    logger.info("Cleaned %d files from results", count)


async def handle_start(update: Update, _) -> None:
    if not is_allowed(update):
        return
    await update.message.reply_text("Use /make <prompt> to generate HTML plugins")


async def post_init(app: Application) -> None:
    """Start background tasks after bot initialization."""
    asyncio.create_task(process_queue())


def main() -> None:
    app = Application.builder().token(TELEGRAM_API_KEY).post_init(post_init).build()

    # Add command handlers
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("make", handle_make))
    app.add_handler(CommandHandler("ai-on", handle_ai_on))
    app.add_handler(CommandHandler("ai-off", handle_ai_off))
    app.add_handler(CommandHandler("ai-clean", handle_ai_clean))

    logger.info("Bot started (AI disabled by default)")
    app.run_polling()


if __name__ == "__main__":
    main()
