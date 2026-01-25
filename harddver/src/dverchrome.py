from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
import subprocess
import socket
import os


def is_vnc_port_taken(host="127.0.0.1", port=5900):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return False
        except OSError:
            return True


def start_chrome():
    subprocess.run(["killall", "-9", "chrome"])
    subprocess.run(["killall", "-9", "chromedriver"])

    os.environ["DISPLAY"] = ":0"
    options = Options()

    if not is_vnc_port_taken():
        options.add_argument("--kiosk")

    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--no-first-run")
    options.add_argument("--disable-infobars")
    options.add_argument("--noerrdialogs")
    options.add_argument("--use-fake-ui-for-media-stream")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    options.add_experimental_option("prefs", {
        "download.default_directory": "/home/kiosk/video",
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "profile.default_content_setting_values.automatic_downloads": 1
    })

    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(DEFAULT_URL)

    return driver


DEFAULT_URL = "http://127.0.0.1:8000/"
