from http.server import HTTPServer, SimpleHTTPRequestHandler
from dverchrome import start_chrome
from dverdata import data_pusher
from functools import partial
from dvertg import start_bot
import threading
import signal
import sys


def cleanup(signum, frame):
    driver.quit()
    sys.exit(0)


def run_http_server():
    handler_class = partial(SimpleHTTPRequestHandler, directory="./static/")
    httpd = HTTPServer(("127.0.0.1", 8000), handler_class)
    httpd.serve_forever()


threading.Thread(target=run_http_server, daemon=True).start()

driver = start_chrome()

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

threading.Thread(target=data_pusher, args=(driver,)).start()

start_bot(driver)
