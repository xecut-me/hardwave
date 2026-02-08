import asyncio
import logging
import os
import re
from pathlib import Path

import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

TELEGRAM_API_KEY = os.environ["TELEGRAM_API_KEY"]
ALLOWED_CHAT_IDS = {int(x) for x in os.environ["ALLOWED_CHAT_IDS"].split(",")}
OPENAI_API_URL = os.environ["OPENAI_API_URL"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")

RESULTS_DIR = Path(__file__).parent / "results"
BASE_PROMPT_PATH = Path(__file__).parent / "base_prompt.txt"


def is_allowed(update: Update) -> bool:
    msg = update.message
    if msg is None:
        return False
    if msg.chat_id not in ALLOWED_CHAT_IDS:
        logger.debug("Rejected: chat_id %s not in allowed list", msg.chat_id)
        return False
    return True


def get_next_id() -> int:
    RESULTS_DIR.mkdir(exist_ok=True)
    existing = [f.stem for f in RESULTS_DIR.glob("*.html")]
    ids = [int(x) for x in existing if x.isdigit()]
    return max(ids, default=0) + 1


async def generate_html(task_id: int, prompt: str) -> str:
    base_prompt = BASE_PROMPT_PATH.read_text()
    full_prompt = f"{base_prompt}\n\n# Task\n\n{prompt}"

    async with httpx.AsyncClient(timeout=300) as client:
        response = await client.post(
            f"{OPENAI_API_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": OPENAI_MODEL,
                "messages": [{"role": "user", "content": full_prompt}],
            },
        )
        response.raise_for_status()
        data = response.json()

    content = data["choices"][0]["message"]["content"]
    match = re.search(r"```html\s*(.*?)\s*```", content, re.DOTALL)
    html = match.group(1) if match else content

    result_path = RESULTS_DIR / f"{task_id}.html"
    result_path.write_text(html)
    return str(result_path)


async def handle_make(update: Update, _) -> None:
    if not is_allowed(update):
        return

    msg = update.message
    text = msg.text or ""
    prompt = text[6:].strip()  # strip "/make "

    if not prompt:
        await msg.reply_text("Usage: /make <prompt>")
        return

    task_id = get_next_id()
    await msg.reply_text(f"Task #{task_id} started")
    logger.info("Task #%d started for user %s: %s", task_id, msg.from_user.id, prompt)

    try:
        result_path = await generate_html(task_id, prompt)
        await msg.reply_text(f"Task #{task_id} completed: {result_path}")
        logger.info("Task #%d completed", task_id)
    except Exception as e:
        logger.error("Task #%d failed: %s", task_id, e)
        await msg.reply_text(f"Task #{task_id} failed: {e}")


async def handle_start(update: Update, _) -> None:
    if not is_allowed(update):
        return
    await update.message.reply_text("Use /make <prompt> to generate HTML plugins")


def main() -> None:
    app = Application.builder().token(TELEGRAM_API_KEY).build()
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("make", handle_make))

    logger.info("Bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
