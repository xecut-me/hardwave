import asyncio
import logging
import os
import re
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

# Environment variables
TELEGRAM_API_KEY = os.environ["TELEGRAM_API_KEY"]
TELEGRAM_CHAT_ID = int(os.environ["TELEGRAM_CHAT_ID"])
TELEGRAM_ADMIN_IDS = {int(x) for x in os.environ["TELEGRAM_ADMIN_IDS"].split(",")}
LLM_API_URL = os.environ["LLM_API_URL"]
LLM_API_KEY = os.environ["LLM_API_KEY"]
LLM_API_MODEL = os.environ.get("LLM_API_MODEL", "claude-3-5-sonnet-20241022")
URL_BASE = "https://xecut-ai-ugc.tgr.rs/"

RESULTS_DIR = Path(__file__).parent / "results"
BASE_PROMPT_PATH = Path(__file__).parent / "base_prompt.md"

# Simple state
ai_enabled = False
task_queue = asyncio.Queue()
is_processing = False


def is_correct_chat(update: Update) -> bool:
    """Check if message is from the correct chat."""
    msg = update.message
    if msg is None:
        return False
    if msg.chat_id != TELEGRAM_CHAT_ID:
        logger.debug("Rejected: chat_id %s != %s", msg.chat_id, TELEGRAM_CHAT_ID)
        return False
    return True


def is_admin(update: Update) -> bool:
    """Check if user is an admin."""
    msg = update.message
    if msg is None or msg.from_user is None:
        return False
    return msg.from_user.id in TELEGRAM_ADMIN_IDS


def _call_api(prompt: str) -> str:
    """Call LLM API synchronously."""
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
    """Generate HTML from prompt and save to file."""
    base_prompt = BASE_PROMPT_PATH.read_text()
    full_prompt = f"{base_prompt}\n\n# Task\n\n{prompt}"

    # Run API call in thread pool
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        content = await loop.run_in_executor(executor, _call_api, full_prompt)

    # Extract HTML from markdown code block
    match = re.search(r"```html\s*(.*?)\s*```", content, re.DOTALL)
    html = match.group(1) if match else content

    # Save to file
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    RESULTS_DIR.mkdir(exist_ok=True)
    result_path = RESULTS_DIR / f"{timestamp}.html"
    result_path.write_text(html)

    return str(result_path), html


async def process_queue():
    """Process tasks from queue one at a time."""
    global is_processing
    while True:
        update, prompt = await task_queue.get()
        is_processing = True
        msg = update.message

        try:
            result_path, html = await generate_html(prompt)
            filename = Path(result_path).name
            url = f"{URL_BASE}{filename}"

            await msg.reply_text(f"ok\n{url}")
            await msg.reply_document(document=open(result_path, "rb"), filename=filename)

            logger.info("Task completed: %s", filename)
        except Exception as e:
            logger.error("Task failed: %s", e, exc_info=True)
            await msg.reply_text("error generating")
        finally:
            is_processing = False
            task_queue.task_done()


async def handle_make(update: Update, _) -> None:
    """Handle /make command to generate HTML."""
    if not is_correct_chat(update):
        return

    msg = update.message

    # Only admins can use /make when AI is disabled
    if not ai_enabled and not is_admin(update):
        return

    text = msg.text or ""
    prompt = text[6:].strip()  # strip "/make "

    if not prompt:
        await msg.reply_text("Usage: /make <prompt>")
        return

    await task_queue.put((update, prompt))
    logger.info("Task queued: %s", prompt)


async def handle_ai_on(update: Update, _) -> None:
    """Enable AI for all users in the chat."""
    global ai_enabled

    if not is_correct_chat(update):
        return

    msg = update.message

    if not is_admin(update):
        return
    if msg.forward_date is not None:
        return

    ai_enabled = True
    await msg.reply_text("AI enabled")
    logger.info("AI enabled")


async def handle_ai_off(update: Update, _) -> None:
    """Disable AI for all users in the chat."""
    global ai_enabled

    if not is_correct_chat(update):
        return

    msg = update.message

    if not is_admin(update):
        return
    if msg.forward_date is not None:
        return

    ai_enabled = False
    await msg.reply_text("AI disabled")
    logger.info("AI disabled")


async def handle_ai_clean(update: Update, _) -> None:
    """Delete all generated HTML files."""
    if not is_correct_chat(update):
        return

    msg = update.message

    if not is_admin(update):
        return

    count = 0
    if RESULTS_DIR.exists():
        for file in RESULTS_DIR.glob("*.html"):
            file.unlink()
            count += 1

    await msg.reply_text(f"Cleaned {count} files")
    logger.info("Cleaned %d files", count)


async def handle_start(update: Update, _) -> None:
    """Handle /start command."""
    if not is_correct_chat(update):
        return
    await update.message.reply_text("Use /make <prompt> to generate HTML plugins")


async def post_init(app: Application) -> None:
    """Start background queue processor."""
    asyncio.create_task(process_queue())


def main() -> None:
    app = Application.builder().token(TELEGRAM_API_KEY).post_init(post_init).build()

    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("make", handle_make))
    app.add_handler(CommandHandler("ai-on", handle_ai_on))
    app.add_handler(CommandHandler("ai-off", handle_ai_off))
    app.add_handler(CommandHandler("ai-clean", handle_ai_clean))

    logger.info("Bot started (AI disabled by default)")
    app.run_polling()


if __name__ == "__main__":
    main()
