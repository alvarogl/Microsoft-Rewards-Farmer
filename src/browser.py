import contextlib
import logging
import random
import uuid
from pathlib import Path
from typing import Any

import ipapi
from playwright.sync_api import sync_playwright

from src.userAgentGenerator import GenerateUserAgent
from src.utils import Utils

class Browser:
    """Playwright wrapper class."""
    
    def __init__(self, mobile: bool, account, args: Any) -> None:
        self.mobile = mobile
        self.browserType = "mobile" if mobile else "desktop"
        self.headless = not args.visible
        self.username = account["username"]
        self.password = account["password"]
        self.localeLang, self.localeGeo = self.getCCodeLang(args.lang, args.geo)
        self.proxy = None
        if args.proxy:
            self.proxy = args.proxy
        elif account.get("proxy"):
            self.proxy = account["proxy"]
        self.userDataDir = self.setupProfiles()
        self.browserConfig = Utils.get_browser_config(self.userDataDir)
        (
            self.userAgent,
            self.userAgentMetadata,
            newBrowserConfig,
        ) = GenerateUserAgent().userAgent(self.browserConfig, mobile)
        if newBrowserConfig:
            self.browserConfig = newBrowserConfig
            Utils.save_browser_config(self.userDataDir, self.browserConfig)
        self.browser = self.browserSetup()
        self.utils = Utils(self.browser)

    def __enter__(self) -> "Browser":
        return self

    def __exit__(self, *args: Any) -> None:
        self.closeBrowser()

    def closeBrowser(self) -> None:
        """Perform actions to close the browser cleanly."""
        # close web browser
        with contextlib.suppress(Exception):
            self.browser.close()

    def browserSetup(self):
        with sync_playwright() as p:
            browserType = p.chromium if not self.mobile else p.webkit
            browser = browserType.launch(headless=self.headless)
            context = browser.new_context(user_agent=self.userAgent, locale=self.localeLang)
            page = context.new_page()
            return page

    def setupProfiles(self) -> Path:
        """
        Sets up the sessions profile for the chrome browser.
        Uses the username to create a unique profile for the session.

        Returns:
            Path
        """
        currentPath = Path(__file__)
        parent = currentPath.parent.parent
        sessionsDir = parent / "sessions"

        sessionUuid = uuid.uuid5(uuid.NAMESPACE_DNS, self.username)
        sessionsDir = sessionsDir / str(sessionUuid) / self.browserType
        sessionsDir.mkdir(parents=True, exist_ok=True)
        return sessionsDir

    def getCCodeLang(self, lang: str, geo: str) -> tuple:
        if lang is None or geo is None:
            try:
                nfo = ipapi.location()
                if isinstance(nfo, dict):
                    if lang is None:
                        lang = nfo["languages"].split(",")[0].split("-")[0]
                    if geo is None:
                        geo = nfo["country"]
            except Exception:  # pylint: disable=broad-except
                return ("en", "US")
        return (lang, geo)
