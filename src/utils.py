import contextlib
import json
import locale as pylocale
import time
import urllib.parse
from pathlib import Path

import requests

from .constants import BASE_URL

class Utils:
    def __init__(self, context):
        self.context = context

    def wait_until_visible(self, selector: str, timeout: float = 10000):
        self.context.wait_for_selector(selector, timeout=timeout)

    def wait_until_clickable(self, selector: str, timeout: float = 10000):
        self.context.wait_for_selector(selector, timeout=timeout).click()

    def wait_for_msreward_element(self, selector: str):
        loading_time_allowed = 5
        refreshes_allowed = 5
        checking_interval = 0.5
        checks = loading_time_allowed / checking_interval
        tries = 0
        refresh_count = 0

        while True:
            try:
                self.context.wait_for_selector(selector)
                return True
            except:
                if tries < checks:
                    tries += 1
                    time.sleep(checking_interval)
                elif refresh_count < refreshes_allowed:
                    self.context.reload()
                    refresh_count += 1
                    tries = 0
                    time.sleep(5)
                else:
                    return False

    def wait_until_question_refresh(self):
        return self.wait_for_msreward_element(".rqECredits")

    def wait_until_quiz_loads(self):
        return self.wait_for_msreward_element('//*[@id="rqStartQuiz"]')

    def reset_tabs(self):
        self.context.new_page().goto('about:blank')

    def go_home(self):
        reload_threshold = 5
        reload_interval = 10
        target_url = urllib.parse.urlparse(BASE_URL)
        self.context.goto(BASE_URL)

        reloads = 0
        interval_count = 0
        while True:
            self.try_dismiss_cookie_banner()
            if self.context.query_selector("#more-activities"):
                break
            
            current_url = urllib.parse.urlparse(self.context.url)
            if current_url.hostname != target_url.hostname and self.try_dismiss_all_messages():
                time.sleep(1)
                self.context.goto(BASE_URL)
            
            time.sleep(1)  # Adjust interval as needed

            interval_count += 1
            if interval_count >= reload_interval:
                interval_count = 0
                reloads += 1
                self.context.reload()
                if reloads >= reload_threshold:
                    break

    def get_answer_code(self, key: str, string: str) -> str:
        t = sum(ord(string[i]) for i in range(len(string)))
        t += int(key[-2:], 16)
        return str(t)

    def get_dashboard_data(self) -> dict:
        return self.context.evaluate("() => window.dashboard")

    def get_bing_info(self):
        cookie_jar = self.context.cookies()
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

    def check_bing_login(self):
        data = self.get_bing_info()
        if data:
            return data["userInfo"]["isRewardsUser"]
        else:
            return False

    def get_account_points(self) -> int:
        return self.get_dashboard_data()["userStatus"]["availablePoints"]

    def get_bing_account_points(self) -> int:
        data = self.get_bing_info()
        if data:
            return data["userInfo"]["balance"]
        else:
            return 0

    def try_dismiss_all_messages(self):
        buttons = [
            'button#iLandingViewAction',
            'button#iShowSkip',
            'button#iNext',
            'button#iLooksGood',
            'button#idSIButton9',
            'button.ms-Button.ms-Button--primary',
        ]
        for button_selector in buttons:
            with contextlib.suppress(Exception):
                self.context.wait_for_selector(button_selector).click()

    def try_dismiss_cookie_banner(self):
        with contextlib.suppress(Exception):
            self.context.wait_for_selector('#cookie-banner button').click()
            time.sleep(2)

    def try_dismiss_bing_cookie_banner(self):
        with contextlib.suppress(Exception):
            self.context.wait_for_selector('#bnp_btn_accept').click()
            time.sleep(2)

    def switch_to_new_tab(self, time_to_wait: int = 0):
        time.sleep(0.5)
        self.context.wait_for_selector('body').eval_on_selector_all('a[target=_blank]', 'links => links[0]?.click()')
        if time_to_wait > 0:
            time.sleep(time_to_wait)

    def close_current_tab(self):
        self.context.close()

    def visit_new_tab(self, time_to_wait: int = 0):
        self.switch_to_new_tab(time_to_wait)
        self.close_current_tab()

    def get_remaining_searches(self):
        dashboard = self.get_dashboard_data()
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

    def format_number(self, number, num_decimals=2):
        return f"{number:,.{num_decimals}f}"

    @staticmethod
    def get_browser_config(session_path: Path) -> dict:
        config_file = session_path.joinpath("config.json")
        if config_file.exists():
            with open(config_file, "r") as f:
                config = json.load(f)
                return config
        else:
            return {}

    @staticmethod
    def save_browser_config(session_path: Path, config: dict):
        config_file = session_path.joinpath("config.json")
        with open(config_file, "w") as f:
            json.dump(config, f)
