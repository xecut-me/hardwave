from telegram.ext import Application, CommandHandler, TypeHandler, ContextTypes
from secret import SECRET_TELEGRAM_API_KEY
from dverchrome import DEFAULT_URL
from dverdata import get_data
from telegram import Update
from io import BytesIO
from PIL import Image
from time import time
from mss import mss
import subprocess
import json
import sys


admin_chat_id = -1002571293789
admin_not_allowed = "Это админская команда, работает только в чате https://t.me/+IBkZEqKkqRlhNGQy"

xecut_chat_id = -1002089160630
xecut_not_allowed = "Эта команда работает в чате хакспейса Xecut https://t.me/xecut_chat"


def allowed_chats_only(allowed_chat_ids=(admin_chat_id,), not_allowed_message=admin_not_allowed):
    def decorator(func):
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            print(json.dumps(update.to_dict(), ensure_ascii=False))

            if update.message.forward_from or update.message.forward_from_chat:
                return
            
            if update.effective_chat.id not in allowed_chat_ids:
                await update.message.reply_text(not_allowed_message)
                return

            await func(update, context)
        return wrapper
    return decorator


@allowed_chats_only()
async def reload_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    driver.refresh()
    await update.message.reply_text("🔄 Страница перезагружена " + state, disable_web_page_preview=True)


@allowed_chats_only()
async def url_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args and not context.args[0].startswith("http"):
        await update.message.reply_text("❌ URL должен начинаться с http")
        return
    
    if context.args:
        url = context.args[0]
        state = f"🌐🧪 Загружен тестовый URL {url}"
    else:
        url = DEFAULT_URL
        state = f"🌐🔒 Загружен продовый URL {url}"
    
    driver.get(url)
    await update.message.reply_text(state, disable_web_page_preview=True)


@allowed_chats_only()
async def deploy_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pullres = subprocess.run(["git", "pull"], capture_output=True, text=True)
    splits = pullres.stdout.strip().split("origin/main")
    split_text = (splits[1] if len(splits) > 1 else splits[0])[0:2000]
    
    driver.quit()

    await update.message.reply_text("\n\n".join([
        "🚀 git pull",
        split_text,
        "🚀 driver.quit() = ok, крешимся для перезапуска супервизором 😂"
    ]))
    
    sys.exit(0)


@allowed_chats_only((admin_chat_id, xecut_chat_id), xecut_not_allowed)
async def screenshot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with mss() as sct:
        screenshot = sct.grab(sct.monitors[0])

    img = Image.frombytes("RGB", (screenshot.width, screenshot.height), screenshot.rgb)
    buffer = BytesIO()
    buffer.name = f"screenshot.png{time()}"
    img.save(buffer, format="PNG")
    buffer.seek(0)

    await update.message.reply_photo(photo=buffer)


@allowed_chats_only((admin_chat_id, xecut_chat_id), xecut_not_allowed)
async def display_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text:
        return
    
    text =  " ".join(update.message.text.split(" ")[1:]).strip()[0:500]

    if not text:
        await update.message.reply_text("Чтобы вывести сообщение напиши /display [ТВОЕ_СООБЩЕНИЕ]")
        return
    
    if not update.message.from_user.username:
        await update.message.reply_text("Заведи пожалуйста юзернейм в настройках телеги")
        return
    
    message = {"username": update.message.from_user.username, "text": text}
    message_json = json.dumps(message, ensure_ascii=False)

    chat_log.write(message_json + "\n")
    chat_log.flush()
    
    driver.execute_script("return onData(arguments[0]);", message_json)

    text = "Спасибо, сообщение добавлено на дверь, заходи посмотреть ;) https://maps.app.goo.gl/8s1x3Zzptt5A8gpc7"
    await update.message.reply_text(text, disable_web_page_preview=True)


@allowed_chats_only()
async def getdata_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_data(), disable_web_page_preview=True)


async def just_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(json.dumps(update.to_dict(), ensure_ascii=False))


async def init(app: Application) -> None:
    result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
    commit_hash = result.stdout.strip()

    text = f"🎉 Я запустился! Версия https://github.com/xecut-me/harddver/tree/{commit_hash}"
    await app.bot.send_message(chat_id=admin_chat_id, text=text, disable_web_page_preview=True)


def start_bot(_driver):
    global driver, chat_log
    driver = _driver

    chat_log = open("./chat.json.log", "a")

    application: Application = Application.builder().token(SECRET_TELEGRAM_API_KEY).post_init(init).build()

    application.add_handler(CommandHandler("display", display_handler))
    application.add_handler(CommandHandler("screenshot", screenshot_handler))
    application.add_handler(CommandHandler("deploy", deploy_handler))
    application.add_handler(CommandHandler("url", url_handler))
    application.add_handler(CommandHandler("reload", reload_handler))
    application.add_handler(CommandHandler("getdata", getdata_handler))
    application.add_handler(TypeHandler(Update, just_log))
    
    application.run_polling()


state = f"🌐🔒 Загружен продовый URL {DEFAULT_URL}"
driver = None
chat_log = None