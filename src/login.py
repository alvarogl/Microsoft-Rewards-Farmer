import contextlib
import logging
import time
import urllib.parse

from src.browser import Browser


class Login:
    def __init__(self, browser: Browser):
        self.browser = browser
        self.page = browser.browser  # Using the browser's page directly
        self.utils = browser.utils

    def login(self):
        logging.info("[LOGIN] " + "Logging-in...")
        self.page.goto(url="https://login.live.com/", wait_until='domcontentloaded')
        alreadyLoggedIn = False
        while True:
            try:
                self.page.locator('html[data-role-name="MeePortal"]').wait_for(10000)
                alreadyLoggedIn = True
                break
            except Exception:  # pylint: disable=broad-except
                try:
                    self.page.locator("#loginHeader").wait_for()
                    break
                except Exception:  # pylint: disable=broad-except
                    if self.utils.tryDismissAllMessages():
                        continue

        if not alreadyLoggedIn:
            self.executeLogin()
        self.utils.tryDismissCookieBanner()

        logging.info("[LOGIN] " + "Logged-in !")

        self.utils.goHome()
        points = self.utils.getAccountPoints()

        logging.info("[LOGIN] " + "Ensuring login on Bing...")
        self.checkBingLogin()
        logging.info("[LOGIN] Logged-in successfully !")
        return points

    def executeLogin(self):
        self.page.locator("#loginHeader").wait_for()
        logging.info("[LOGIN] " + "Writing email...")
        self.page.locator('input[name="loginfmt"]').fill(self.browser.username)
        self.page.locator("#idSIButton9").click()

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
            self.page.wait_for_load_state()
            self.utils.tryDismissAllMessages()
            time.sleep(10)

        self.page.locator('html[data-role-name="MeePortal"]').wait_for()

    def enterPassword(self, password):
        self.page.locator('input[name="passwd"]').wait_for()
        self.page.locator("#idSIButton9").wait_for()
        # browser.webdriver.find_element(By.NAME, "passwd").send_keys(password)
        # If password contains special characters like " ' or \, send_keys() will not work
        password = password.replace("\\", "\\\\").replace('"', '\\"')
        self.page.locator('input[name="passwd"]').fill(password)

        logging.info("[LOGIN] " + "Writing password...")
        self.page.locator("#idSIButton9").click()
        time.sleep(3)

    def checkBingLogin(self):
        while True:
            currentUrl = urllib.parse.urlparse(self.page.url)
            if currentUrl.hostname == "www.bing.com" and currentUrl.path == "/":
                time.sleep(3)
                self.utils.tryDismissBingCookieBanner()
                with contextlib.suppress(Exception):
                    if self.utils.checkBingLogin():
                        return
            time.sleep(1)
            self.page.goto(
                url="https://www.bing.com/fd/auth/signin?action=interactive&provider=windows_live_id&return_url=https%3A%2F%2Fwww.bing.com%2F",
                wait_until='domcontentloaded'
            )
