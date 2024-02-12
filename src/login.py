import contextlib
import logging
import time
import urllib.parse

from playwright.sync_api import sync_playwright

from src.browser import Browser


class Login:
    def __init__(self, browser: Browser):
        self.browser = browser
        self.page = browser.browser  # Using the browser's page directly
        self.utils = browser.utils

    def login(self):
        logging.info("[LOGIN] " + "Logging-in...")
        self.page.goto("https://login.live.com/")
        alreadyLoggedIn = False
        while True:
            try:
                self.page.wait_for_selector('html[data-role-name="MeePortal"]')
                alreadyLoggedIn = True
                break
            except Exception:  # pylint: disable=broad-except
                try:
                    self.page.wait_for_selector("#loginHeader")
                    break
                except Exception:  # pylint: disable=broad-except
                    if self.utils.try_dismiss_all_messages():
                        continue

        if not alreadyLoggedIn:
            self.executeLogin()
        self.utils.try_dismiss_cookie_banner()

        logging.info("[LOGIN] " + "Logged-in !")

        self.utils.go_home()
        points = self.utils.get_account_points()

        logging.info("[LOGIN] " + "Ensuring login on Bing...")
        self.checkBingLogin()
        logging.info("[LOGIN] Logged-in successfully !")
        return points

    def executeLogin(self):
        self.page.wait_for_selector("#loginHeader")
        logging.info("[LOGIN] " + "Writing email...")
        self.page.fill('input[name="loginfmt"]', self.browser.username)
        self.page.click("#idSIButton9")

        try:
            self.enterPassword(self.browser.password)
        except Exception:  # pylint: disable=broad-except
            logging.error("[LOGIN] " + "2FA required !")
            with contextlib.suppress(Exception):
                code = self.page.inner_html("#idRemoteNGC_DisplaySign")
                logging.error("[LOGIN] " + f"2FA code: {code}")
            logging.info("[LOGIN] Press enter when confirmed...")
            input()

        while not (
            urllib.parse.urlparse(self.page.url).path == "/"
            and urllib.parse.urlparse(self.page.url).hostname
            == "account.microsoft.com"
        ):
            self.utils.try_dismiss_all_messages()
            time.sleep(1)

        self.page.wait_for_selector('html[data-role-name="MeePortal"]')

    def enterPassword(self, password):
        self.page.wait_for_selector('input[name="passwd"]')
        self.page.wait_for_selector("#idSIButton9")
        # browser.webdriver.find_element(By.NAME, "passwd").send_keys(password)
        # If password contains special characters like " ' or \, send_keys() will not work
        password = password.replace("\\", "\\\\").replace('"', '\\"')
        self.page.evaluate(
            f'document.getElementsByName("passwd")[0].value = "{password}";'
        )
        logging.info("[LOGIN] " + "Writing password...")
        self.page.click("#idSIButton9")
        time.sleep(3)

    def checkBingLogin(self):
        self.page.goto(
            "https://www.bing.com/fd/auth/signin?action=interactive&provider=windows_live_id&return_url=https%3A%2F%2Fwww.bing.com%2F"
        )
        while True:
            currentUrl = urllib.parse.urlparse(self.page.url)
            if currentUrl.hostname == "www.bing.com" and currentUrl.path == "/":
                time.sleep(3)
                self.utils.try_dismiss_cookie_banner()
                with contextlib.suppress(Exception):
                    if self.utils.check_bing_login():
                        return
            time.sleep(1)
