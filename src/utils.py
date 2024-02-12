import contextlib
import json
import time
import urllib.parse
from pathlib import Path

import requests

from .constants import BASE_URL


class Utils:
    def __init__(self, page):
        self.page = page

    def waitUntilVisible(self, selector: str, timeout: float = 10000):
        self.page.wait_for_selector(selector, timeout=timeout)

    def waitUntilClickable(self, selector: str, timeout: float = 10000):
        self.page.wait_for_selector(selector, timeout=timeout).click()

    def waitForMsrewardElement(self, selector: str):
        loading_time_allowed = 5
        refreshes_allowed = 5
        checking_interval = 0.5
        checks = loading_time_allowed / checking_interval
        tries = 0
        refresh_count = 0

        while True:
            try:
                self.page.wait_for_selector(selector)
                return True
            except:
                if tries < checks:
                    tries += 1
                    time.sleep(checking_interval)
                elif refresh_count < refreshes_allowed:
                    self.page.reload()
                    refresh_count += 1
                    tries = 0
                    time.sleep(5)
                else:
                    return False

    def waitUntilQuestionRefresh(self):
        return self.waitForMsrewardElement(".rqECredits")

    def waitUntilQuizLoads(self):
        return self.waitForMsrewardElement('//*[@id="rqStartQuiz"]')

    def resetTabs(self):
        self.page.new_page().goto('about:blank')

    def goHome(self):
        reload_threshold = 5
        reload_interval = 10
        target_url = urllib.parse.urlparse(BASE_URL)
        self.page.goto(BASE_URL)

        reloads = 0
        interval_count = 0
        while True:
            self.tryDismissCookieBanner()
            if self.page.query_selector("#more-activities"):
                break

            current_url = urllib.parse.urlparse(self.page.url)
            if current_url.hostname != target_url.hostname and self.tryDismissAllMessages():
                time.sleep(1)
                self.page.goto(BASE_URL)

            time.sleep(1)  # Adjust interval as needed

            interval_count += 1
            if interval_count >= reload_interval:
                interval_count = 0
                reloads += 1
                self.page.reload()
                if reloads >= reload_threshold:
                    break

    def getAnswerCode(self, key: str, string: str) -> str:
        t = sum(ord(string[i]) for i in range(len(string)))
        t += int(key[-2:], 16)
        return str(t)

    def getDashboardData(self) -> dict:
        return self.page.evaluate("() => window.dashboard")

    def getBingInfo(self):
        cookie_jar = self.page.context.cookies()
        cookies = {cookie["name"]: cookie["value"] for cookie in cookie_jar}
        tries = 0
        max_tries = 5

        while tries < max_tries:
            with contextlib.suppress(Exception):
                response = requests.get(
                    "https://www.bing.com/rewards/panelflyout/getuserinfo",
                    cookies=cookies,
                )
                if response.status_code == requests.codes.ok:
                    data = response.json()
                    return data
                else:
                    pass
            tries += 1
            time.sleep(1)
        return None

    def checkBingLogin(self):
        data = self.getBingInfo()
        if data:
            return data["userInfo"]["isRewardsUser"]
        else:
            return False

    def getAccountPoints(self) -> int:
        return self.getDashboardData()["userStatus"]["availablePoints"]

    def getBingAccountPoints(self) -> int:
        data = self.getBingInfo()
        if data:
            return data["userInfo"]["balance"]
        else:
            return 0

    def tryDismissAllMessages(self):
        buttons = [
            'xpath=//*[@id="acceptButton"]',
            'button#iLandingViewAction',
            'button#iShowSkip',
            'button#iNext',
            'button#iLooksGood',
            'button#idSIButton9'
        ]
        found = False
        for button_selector in buttons:
            if not found:
                for elem in self.page.locator(button_selector).all():
                    elem.click()
                    found = True
                    break


    def tryDismissCookieBanner(self):
        with contextlib.suppress(Exception):
            self.page.locator('#cookie-banner button').first.click()
            time.sleep(2)

    def tryDismissBingCookieBanner(self):
        with contextlib.suppress(Exception):
            self.page.locator('#bnp_btn_accept').click()
            time.sleep(2)

    def switchToNewTab(self, timeToWait: int = 0):
        time.sleep(0.5)
        self.page.locator('body').wait_for().eval_on_selector_all('a[target=_blank]', 'links => links[0]?.click()')
        if timeToWait > 0:
            time.sleep(timeToWait)

    def closeCurrentTab(self):
        self.page.close()

    def visitNewTab(self, time_to_wait: int = 0):
        self.switchToNewTab(time_to_wait)
        self.closeCurrentTab()

    def getRemainingSearches(self):
        dashboard = self.getDashboardData()
        search_points = 1
        counters = dashboard["userStatus"]["counters"]

        if "pcSearch" not in counters:
            return 0, 0
        progress_desktop = 0

        for item in counters['pcSearch']:
            progress_desktop += item.get('pointProgress', 0)

        target_desktop = 0

        for item in counters['pcSearch']:
            target_desktop += item.get('pointProgressMax', 0)

        if target_desktop in [33, 102]:
            # Level 1 or 2 EU/South America
            search_points = 3
        elif target_desktop == 55 or target_desktop >= 170:
            # Level 1 or 2 US
            search_points = 5
        remaining_desktop = int((target_desktop - progress_desktop) / search_points)
        remaining_mobile = 0
        if dashboard["userStatus"]["levelInfo"]["activeLevel"] != "Level1":
            progress_mobile = counters["mobileSearch"][0]["pointProgress"]
            target_mobile = counters["mobileSearch"][0]["pointProgressMax"]
            remaining_mobile = int((target_mobile - progress_mobile) / search_points)
        return remaining_desktop, remaining_mobile

    def formatNumber(self, number, num_decimals=2):
        return f"{number:,.{num_decimals}f}"

    @staticmethod
    def getBrowserConfig(session_path: Path) -> dict:
        config_file = session_path.joinpath("config.json")
        if config_file.exists():
            with open(config_file, "r") as f:
                config = json.load(f)
                return config
        else:
            return {}

    @staticmethod
    def saveBrowserConfig(session_path: Path, config: dict):
        config_file = session_path.joinpath("config.json")
        with open(config_file, "w") as f:
            json.dump(config, f)
