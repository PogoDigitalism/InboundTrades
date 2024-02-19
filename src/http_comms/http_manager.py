from typing import MutableMapping
import urllib.request as request
import urllib.parse as parse
import http.cookiejar as cookiejar

from data.data_manager import DataManager


class HttpManager:
    def __init__(self) -> None:
        self._jar = cookiejar.CookieJar()
        self._headers: MutableMapping[str, str] = {}

    def _get_xcsrf(self):
        self._xcsrf = ...

    def _set_cookie(self) -> None:
        parsed = DataManager.get_data()
        cookie_str = parsed[".ROBLOSECURITY"]

        cookie = cookiejar.Cookie(name=".ROBLOSECURITY", value=cookie_str, domain="https://www.roblox.com/trades")
        self._jar.set_cookie(cookie=cookie)

    def start_session(self):
        ...

    def validate_cookie(self):
        ...