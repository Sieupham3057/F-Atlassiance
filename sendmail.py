#!/usr/bin/env python3
"""
pritunl_selenium_automation.py

- Đăng nhập Pritunl web UI (headless Chrome)
- Vào trang Users, lấy danh sách users hiển thị
- Mở từng user, click Download Profile (nếu có), lưu file vào OUT_DIR
- (Tuỳ chọn) gửi email kèm profile bằng SMTP (bật SEND_EMAIL=True)
- Bạn phải điều chỉnh selectors cho đúng UI của server bạn.
"""

import os
import time
import re
import logging
from typing import Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
import smtplib
from email.message import EmailMessage

# ---------- CONFIG ----------
BASE_URL = "https://ovpn.fint.vn/"  # ví dụ
USERNAME = os.environ.get("PRITUNL_USER", "admin")
PASSWORD = os.environ.get("PRITUNL_PASS", "Fintsoft@2019")
OUT_DIR = os.path.abspath("./downloads")
HEADLESS = True
SEND_EMAIL = False  # bật nếu muốn gửi email tự động
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "huongdx@fint.vn"
SMTP_PASS = "Conchodungo"
EMAIL_FROM = "VPN Admin <huongdx@fint.vn>"

# Selectors — cần kiểm tra trên UI của bạn
USERS_PAGE = "/#/users"   # hoặc đường dẫn đúng với UI
# selector cho từng hàng user (thử sửa nếu khác)
USER_ROW_SELECTOR = "table tbody tr"  # mặc định đọc toàn bộ table rows
# trong mỗi row, xác định ô email (có thể dùng nth-child hoặc query text)
EMAIL_CELL_XPATH = ".//td[contains(., '@')]"  # tìm ô chứa @
# Khi click row, modal hoặc page user hiện ra — selector nút download profile
DOWNLOAD_BUTTON_SELECTORS = [
    "button.download-profile",                 # ví dụ
    "button[title*='Download']",               # thử theo title
    "//a[contains(translate(., 'PROFILE', 'profile'), 'profile')]",  # XPath fallback
    "//button[contains(translate(., 'DOWNLOAD', 'download'), 'download')]"
]
# timeout
WAIT_TIMEOUT = 12

# ---------- end CONFIG ----------

os.makedirs(OUT_DIR, exist_ok=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def setup_driver(headless=True, out_dir=OUT_DIR):
    chrome_opts = Options()
    if headless:
        chrome_opts.add_argument("--headless=new")
    chrome_opts.add_argument("--window-size=1400,1000")
    # allow downloading to folder without prompt
    prefs = {
        "download.default_directory": out_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_opts.add_experimental_option("prefs", prefs)
    # nếu server self-signed: (KHÔNG KHUYẾN KHÍCH, insecure)
    # chrome_opts.add_argument("--ignore-certificate-errors")
    chrome_opts.add_argument("--no-sandbox")
    chrome_opts.add_argument("--disable-dev-shm-usage")
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_opts)
    driver.implicitly_wait(3)
    return driver


def login(driver):
    logging.info("Open login page: %s", BASE_URL)
    driver.get(BASE_URL)
    wait = WebDriverWait(driver, WAIT_TIMEOUT)
    # --- TRY COMMON LOGIN PATTERNS ---
    try:
        # cố gắng tìm input email/username
        # 1) input[name="email"]
        el = wait.until(EC.presence_of_element_located((By.NAME, "email")))
        el.clear(); el.send_keys(USERNAME)
        pw = driver.find_element(By.NAME, "password")
        pw.clear(); pw.send_keys(PASSWORD)
        pw.send_keys(Keys.ENTER)
        logging.info("Submitted login form (using name=email).")
        return True
    except Exception:
        pass

    # fallback generic: input[type="email"] / input[type="password"]
    try:
        email_el = driver.find_element(By.CSS_SELECTOR, 'input[type="email"], input[name="username"], input[name="user"]')
        password_el = driver.find_element(By.CSS_SELECTOR, 'input[type="password"]')
        email_el.clear(); email_el.send_keys(USERNAME)
        password_el.clear(); password_el.send_keys(PASSWORD)
        # try to find login button
        try:
            btn = driver.find_element(By.XPATH, "//button[contains(translate(., 'login', 'LOGIN'), 'login') or contains(., 'Sign In') or contains(., 'Sign in')]")
            btn.click()
        except Exception:
            password_el.send_keys(Keys.ENTER)
        logging.info("Submitted login using generic selectors.")
        return True
    except Exception as e:
        logging.error("Cannot locate login fields: %s", e)
        return False


def wait_for_downloads(out_dir, timeout=30):
    """
    Wait until no .crdownload files remain (Chrome temp) or until timeout.
    """
    start = time.time()
    while time.time() - start < timeout:
        files = os.listdir(out_dir)
        if any(f.endswith(".crdownload") for f in files):
            time.sleep(0.5)
            continue
        # optionally ensure new files exist — just return
        return True
    return False


def try_click_download(driver):
    """Try different selectors to click download."""
    for sel in DOWNLOAD_BUTTON_SELECTORS:
        try:
            if sel.startswith("//"):
                el = driver.find_element(By.XPATH, sel)
            else:
                el = driver.find_element(By.CSS_SELECTOR, sel)
            el.click()
            logging.info("Clicked download using selector: %s", sel)
            return True
        except Exception:
            continue
    # fallback: find any anchor with 'profile' or 'download' in href/text
    try:
        anchors = driver.find_elements(By.TAG_NAME, "a")
        for a in anchors:
            href = (a.get_attribute("href") or "").lower()
            text = (a.text or "").lower()
            if "profile" in href or "profile" in text or "download" in text or "download" in href:
                try:
                    a.click()
                    logging.info("Clicked fallback anchor for download: %s", href or text)
                    return True
                except Exception:
                    continue
    except Exception:
        pass
    logging.debug("No download button found with available selectors.")
    return False


def extract_email_from_row(row) -> Optional[str]:
    """Try to find an email-like cell inside the row element."""
    try:
        cells = row.find_elements(By.XPATH, ".//td")
        for c in cells:
            txt = c.text.strip()
            if re.search(r"[^@\s]+@[^@\s]+\.[^@\s]+", txt):
                return txt
        # fallback: use row text
        t = row.text
        m = re.search(r"[^@\s]+@[^@\s]+\.[^@\s]+", t)
        if m:
            return m.group(0)
    except Exception:
        return None
    return None


def send_email_with_attachment(to_addr: str, subject: str, body: str, attachment_path: Optional[str]):
    if not SEND_EMAIL:
        logging.info("SEND_EMAIL=False, skipping sending to %s", to_addr)
        return
    msg = EmailMessage()
    msg["From"] = EMAIL_FROM
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content(body)
    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, "rb") as f:
            data = f.read()
            msg.add_attachment(data, maintype="application", subtype="octet-stream", filename=os.path.basename(attachment_path))
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(SMTP_USER, SMTP_PASS)
        smtp.send_message(msg)
    logging.info("Email sent to %s", to_addr)


def main():
    driver = setup_driver(HEADLESS, OUT_DIR)
    try:
        ok = login(driver)
        if not ok:
            logging.error("Login failed. Exiting.")
            return

        # đi tới trang users
        driver.get(BASE_URL + USERS_PAGE)
        wait = WebDriverWait(driver, WAIT_TIMEOUT)
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, USER_ROW_SELECTOR)))
        except TimeoutException:
            logging.warning("No user rows found with selector %s — continue anyway.", USER_ROW_SELECTOR)

        rows = driver.find_elements(By.CSS_SELECTOR, USER_ROW_SELECTOR)
        logging.info("Found %d rows (selector: %s).", len(rows), USER_ROW_SELECTOR)
        for idx, row in enumerate(rows):
            try:
                email = extract_email_from_row(row) or f"user_{idx}"
                logging.info("[%d] Processing row: email=%s", idx, email)
                # click the row to open user panel (some UIs require opening)
                try:
                    row.click()
                except Exception:
                    driver.execute_script("arguments[0].click();", row)
                time.sleep(0.8)

                # attempt to click download
                if try_click_download(driver):
                    # wait for download to complete
                    wait_for_downloads(OUT_DIR, timeout=25)
                    # find newest file in OUT_DIR
                    files = [os.path.join(OUT_DIR, f) for f in os.listdir(OUT_DIR) if not f.endswith(".crdownload")]
                    if files:
                        newest = max(files, key=os.path.getmtime)
                        logging.info("Downloaded file for %s -> %s", email, newest)
                        send_email_with_attachment(email, "Your VPN profile", "Please find attached your VPN profile.", newest)
                    else:
                        logging.warning("No downloaded file detected after clicking download for %s", email)
                else:
                    logging.info("No download button for %s (may require deeper navigation).", email)

                # close modal or go back if needed (practical UIs use a close button)
                # Try to close modal with button[text()='Close'] or class close
                try:
                    close_btn = driver.find_element(By.XPATH, "//button[contains(., 'Close') or contains(., 'close') or contains(., 'Cancel') or contains(@class, 'close')]")
                    close_btn.click()
                except Exception:
                    # fallback navigate back to users page
                    driver.get(BASE_URL + USERS_PAGE)
                    time.sleep(0.6)

            except Exception as e:
                logging.exception("Error processing row %d: %s", idx, e)

    finally:
        driver.quit()


if __name__ == "__main__":
    main()

