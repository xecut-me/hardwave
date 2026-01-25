import datetime, hashlib, base64, segno, hmac, time
from secret import TIGOR_XECUT_SECRET


def sign_token_v1(user_id: str, priority: int = 1, max_daily_messages: int = 100, max_tokens: int = 4096, valid_days: int = 7, authority: str = "xecut"):
    values = [user_id, priority, max_daily_messages, max_tokens, authority]
    user_id, priority, max_daily_messages, max_tokens, authority = [str(value).replace("|", "_") for value in values]

    valid_until = (datetime.date.today() + datetime.timedelta(days=valid_days)).strftime("%Y-%m-%d")
    version = "v1"

    message = user_id + "|" + priority + "|" + max_daily_messages + "|" + max_tokens + "|" + valid_until + "|" + version + "|" + authority

    signature_raw = hmac.new(TIGOR_XECUT_SECRET.encode(), message.encode(), hashlib.sha256).digest()
    signature = base64.urlsafe_b64encode(signature_raw).decode()

    return message + "|" + signature


def get_ai_token():
    token = "sms:tigor_ai_token&body=" + sign_token_v1("xecut_" + str((time.time() // 60 * 60) % 10))

    qr = segno.make(token, error='M')

    return qr.svg_data_uri(scale=12, border=0, dark="#0f0", light="#000", unit='px')
