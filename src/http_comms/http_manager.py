import asyncio
import typing
from time import time
import json
import urllib.request as request
import urllib.parse as parse
import urllib.response as response
import urllib.error as error
import http.cookiejar as cookiejar
import http.client as client
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from data import DataManager
from utils import SyncInAsync
from log_comms import Log

Success: typing.TypeAlias = bool

TRADE_URL = "https://trades.roblox.com/v1/trades/inbound?cursor=&limit=25&sortOrder=Desc"
XCSRF_URL = "https://auth.roblox.com/v2/logout"
XCSRF_REFRESH_TIME = 25*60

@dataclass
class InboundData:
    username: str
    user_id: int

    offer_items: list[int] = None
    request_items: list[int] = None

    offer_robux: int = None
    request_robux: int = None


class HttpManager:
    def __init__(self) -> None:
        self._loop = asyncio.get_event_loop()
        self.sync_in_async = SyncInAsync(POOL=ThreadPoolExecutor())

        self._headers: typing.MutableMapping[str, str] = {}
        self._jar = cookiejar.CookieJar()
        self._set_cookie()

        self._opener = request.build_opener(request.HTTPCookieProcessor(self._jar))

        self._xcsrf = None # created in __init__ and not initialize_session due to cookie validation

    def initialize_session(self):
        self._refresh_task = self._loop.create_task(self._refresh_xcsrf())
        self._cached_inbound_id_list: list[int] = list()

    def _set_cookie(self) -> None:
        parsed = DataManager.get_data()
        self._cookie_str = parsed[".ROBLOSECURITY"]

        # cookie = cookiejar.Cookie(name=".ROBLOSECURITY", value=self._cookie_str, domain=TRADE_URL)
        # self._jar.set_cookie(cookie=cookie)

    def _get_xcsrf(self) -> Success:
        request_struct = request.Request(url=XCSRF_URL, method="POST")
        request_struct.add_header("Cookie", f".ROBLOSECURITY={self._cookie_str}")

        try:
            resp = Log.wrap_http(self._opener.open, request_struct=request_struct, success_codes=[403])
        except error.HTTPError as resp:
            match resp.code:
                case 403:
                    self._xcsrf = resp.headers.get("x-csrf-token", failobj=None)
                    return True

                case _:
                    return False

    async def _refresh_xcsrf(self):
        while True:
            if not self._xcsrf: # to avoid too many calls if a validation has been done recently.
                result = await self.sync_in_async.Call(self._get_xcsrf)
                if not result:
                    ...
                    # INVALID XCSRF STUFF

            self._xcsrf = None
            await asyncio.sleep(XCSRF_REFRESH_TIME)

    def _get_inbound_trades(self):
        request_struct = request.Request(url=TRADE_URL, method="GET")
        print(self._cookie_str, self._xcsrf)
        request_struct.add_header("Cookie", f".ROBLOSECURITY={self._cookie_str}")
        request_struct.add_header("x-csrf-token", self._xcsrf)
        request_struct.add_header("content-type", "application/json")

        try:
            resp = Log.wrap_http(self._opener.open, request_struct=request_struct, success_codes=[200, 201])
        except error.HTTPError as resp:
            match resp.code:
                case 403:
                    self._get_xcsrf()
                    return False

                case _:

                    return False
        else:
            response_content = resp.read()
            json_response = json.loads(response_content.decode('utf-8'))
            return json_response

    async def check_inbound_trades(self) -> list[InboundData] | None:
        inbound_data_list: list[InboundData] = list()
        inbound_trades_list = await self.sync_in_async.Call(self._get_inbound_trades)

        new_inbounds_list = []

        if self._cached_inbound_id_list and any(new_inbounds := [inbound for inbound in inbound_trades_list["data"] if not inbound["id"] in self._cached_inbound_id_list]):
            new_inbounds_list = [inbound['id'] for inbound in new_inbounds]
            for inbound in new_inbounds:
                inbound_data = InboundData(username=inbound["user"]["name"],
                                           user_id=inbound["user"]["id"])
                inbound_data_list.append(inbound_data)

        self._cached_inbound_id_list.extend(new_inbounds_list)
        return inbound_data_list

    def quit_session(self):
        self._opener.close()
        self._refresh_task.cancel()

    def validate_cookie(self):
        return self._get_xcsrf()
