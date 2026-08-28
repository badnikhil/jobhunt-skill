"""Firefox driver helper for job-hunt automation.

Snap-packaged Firefox needs an explicit binary path, and geckodriver must match
the Firefox major version or you get opaque session errors.
"""
import os
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

ROOT        = os.environ.get("JOBHUNT_ROOT", os.path.expanduser("~/jobhunt"))
FIREFOX_BIN = os.environ.get("FIREFOX_BIN", "/snap/firefox/current/usr/lib/firefox/firefox")
GECKODRIVER = os.environ.get("GECKODRIVER", f"{ROOT}/tools/geckodriver")

def make_driver(headless=True, profile=None, width=1500, height=1000):
    opts = Options()
    if headless:
        opts.add_argument("--headless")
    if os.path.exists(FIREFOX_BIN):
        opts.binary_location = FIREFOX_BIN
    if profile:                       # reuse a cloned, already-logged-in profile
        opts.add_argument("-profile"); opts.add_argument(profile)
    svc = Service(executable_path=GECKODRIVER) if os.path.exists(GECKODRIVER) else None
    d = webdriver.Firefox(options=opts, service=svc) if svc else webdriver.Firefox(options=opts)
    d.set_window_size(width, height)
    d.set_page_load_timeout(90)
    return d

def body_text(d):
    try:    return d.find_element(By.TAG_NAME, "body").text
    except Exception: return ""

def wait_css(d, css, timeout=25):
    return WebDriverWait(d, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, css)))
