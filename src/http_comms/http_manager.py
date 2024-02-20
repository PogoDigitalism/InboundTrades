import asyncio
import typing
import sys
import json
import time
import urllib.request as request
import urllib.parse as parse
import urllib.response as response
import urllib.error as error
import http.cookiejar as cookiejar
import http.client as client
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from win_comms import ToastManager
from data import DataManager
from utils import SyncInAsync, parse_query_params
from log_comms import Log

Success: typing.TypeAlias = bool

TRADE_URL = "https://trades.roblox.com/v1/trades/inbound?cursor=&limit=25&sortOrder=Desc"
TRADE_INFO_URL = f"https://trades.roblox.com/v1/trades/$id$"

XCSRF_URL = "https://auth.roblox.com/v2/logout"
VALUE_LIST_URL = "https://api.rolimons.com/items/v1/itemdetails"

XCSRF_REFRESH_TIME = 25*60
ROLIVALUES_REFRESH_TIME = 1*60

@dataclass
class InboundData:
    username: str
    user_id: int

    give_value: int = None
    receive_value: int = None

    give_items: list[int] = None
    receive_items: list[int] = None

    give_robux: int = None
    receive_robux: int = None


class HttpManager:
    def __init__(self):
        self._loop = asyncio.get_event_loop()
        self.sync_in_async = SyncInAsync(POOL=ThreadPoolExecutor())

        self._headers: typing.MutableMapping[str, str] = {}
        self._jar = cookiejar.CookieJar()
        self._set_cookie()

        self._opener = request.build_opener(request.HTTPCookieProcessor(self._jar))

        self._value_list = dict()
        self._xcsrf = None # created in __init__ and not initialize_session due to cookie validation

    def initialize_session(self) -> None:
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

    async def _refresh_xcsrf(self) -> None:
        while True:
            if not self._xcsrf: # to avoid too many calls if a validation has been done recently.
                result = await self.sync_in_async.Call(self._get_xcsrf)
                if not result:
                    ...
                    # INVALID XCSRF STUFF

            await asyncio.sleep(XCSRF_REFRESH_TIME)
            self._xcsrf = None

    def _get_value_list(self) -> Success:
        request_struct = request.Request(url=VALUE_LIST_URL, method="GET")

        try:
            resp = Log.wrap_http(self._opener.open, request_struct=request_struct, success_codes=[])
        except error.HTTPError as resp:
            match resp.code:
                case _:
                    return False
        else:
            response_content = resp.read()
            json_response = json.loads(response_content.decode('utf-8'))

            if json_response["success"]:
                self._value_list = json_response["items"]
                return True
            else:
                return False

    async def refresh_valuelist(self):
        while True:
            success = await self.sync_in_async.Call(self._get_value_list)

            await asyncio.sleep(ROLIVALUES_REFRESH_TIME)

    def _items_to_value(self, trade_info: dict) -> tuple[int , int] | tuple[str, str]:
        if self._value_list:
            give_list = trade_info["offers"][0]["userAssets"]
            receive_list = trade_info["offers"][1]["userAssets"]

            give_value = 0
            for asset_data in give_list:
                asset_value = self._value_list[str(asset_data["assetId"])][4]
                give_value += asset_value

            receive_value = 0
            for asset_data in receive_list:
                asset_value = self._value_list[str(asset_data["assetId"])][4]
                receive_value += asset_value

            return (give_value, receive_value)
        else:
            return ("-", "-")

    def _get_trade_info(self, id: int) -> dict | bool:
        parsed_url = parse_query_params(TRADE_INFO_URL, {"id": id})

        request_struct = request.Request(url=parsed_url, method="GET")
        request_struct.add_header("Cookie", f".ROBLOSECURITY={self._cookie_str}")
        request_struct.add_header("x-csrf-token", self._xcsrf)
        request_struct.add_header("content-type", "application/json")

        try:
            resp = Log.wrap_http(self._opener.open, request_struct=request_struct, success_codes=[200, 201])
        except error.HTTPError as resp:
            match resp.code:
                case 403:
                    self._get_xcsrf()

                case 401:
                    toast = ToastManager.spawn_toast("Cookie has been invalided. Please restart your app.", "Cookie invalidated", 5)
                    sys.exit()

                case _:
                    ...

            return False
        else:
            response_content = resp.read()
            json_response = json.loads(response_content.decode('utf-8'))

            return json_response

    def _get_inbound_trades(self) -> dict | bool:
        request_struct = request.Request(url=TRADE_URL, method="GET")
        request_struct.add_header("Cookie", f".ROBLOSECURITY={self._cookie_str}")
        request_struct.add_header("x-csrf-token", self._xcsrf)
        request_struct.add_header("content-type", "application/json")

        try:
            resp = Log.wrap_http(self._opener.open, request_struct=request_struct, success_codes=[200, 201])
        except error.HTTPError as resp:
            match resp.code:
                case 403:
                    self._get_xcsrf()

                case 401:
                    toast = ToastManager.spawn_toast("Cookie has been invalided. Please restart your app.", "Cookie invalidated", 5)
                    sys.exit()

                case _:
                    ...

            return False
        else:
            response_content = resp.read()
            json_response = json.loads(response_content.decode('utf-8'))

            return json_response

    async def check_inbound_trades(self) -> list[InboundData] | None:
        inbound_data_list: list[InboundData] = list()
        inbound_trades_list = await self.sync_in_async.Call(self._get_inbound_trades)
        if not inbound_trades_list:
            return inbound_data_list

        new_inbounds_list = []

        # inbound_id_list = [inbound["id"] for inbound in inbound_trades_list["data"]]
        # if self._cached_inbound_id_list and any(new_inbounds := [inbound for inbound in inbound_trades_list["data"] if not inbound["id"] in self._cached_inbound_id_list]):
        #     new_inbounds_list = [inbound['id'] for inbound in new_inbounds]

        #     Log.info(f"New inbounds detected: {new_inbounds_list}")

        #     for inbound in new_inbounds:
        #         inbound_trade_info = await self.sync_in_async.Call(self._get_trade_info, id=inbound["id"])
        #         if inbound_trade_info:
        #             give_value, receive_value = self._items_to_value(trade_info=inbound_trade_info)

        #             inbound_data = InboundData(
        #                                     username=inbound["user"]["name"],
        #                                     user_id=inbound["user"]["id"],

        #                                     give_items=inbound_trade_info["offers"][0]["userAssets"],
        #                                     give_value=give_value,
        #                                     give_robux=inbound_trade_info["offers"][0]["robux"],
                                            
        #                                     receive_items=inbound_trade_info["offers"][1]["userAssets"],
        #                                     receive_value=receive_value,
        #                                     receive_robux=inbound_trade_info["offers"][1]["robux"],
        #                                     )          
        #         else:
        #             inbound_data = InboundData(
        #                                     username=inbound["user"]["name"],
        #                                     user_id=inbound["user"]["id"],

        #                                     give_items=[],
        #                                     give_value="-",
        #                                     give_robux="-",
                                            
        #                                     receive_items=[],
        #                                     receive_value="-",
        #                                     receive_robux="-",
        #                                     )                   
        #         inbound_data_list.append(inbound_data)

        # self._cached_inbound_id_list.extend(new_inbounds_list) if self._cached_inbound_id_list else self._cached_inbound_id_list.extend(inbound_id_list)

        ## for testing purposes
        for inbound in inbound_trades_list["data"][:1]:
            inbound_trade_info = await self.sync_in_async.Call(self._get_trade_info, id=inbound["id"])
            if inbound_trade_info:
                give_value, receive_value = self._items_to_value(trade_info=inbound_trade_info)

                inbound_data = InboundData(
                                        username=inbound["user"]["name"],
                                        user_id=inbound["user"]["id"],

                                        give_items=inbound_trade_info["offers"][0]["userAssets"],
                                        give_value=give_value,
                                        give_robux=inbound_trade_info["offers"][0]["robux"],
                                        
                                        receive_items=inbound_trade_info["offers"][1]["userAssets"],
                                        receive_value=receive_value,
                                        receive_robux=inbound_trade_info["offers"][1]["robux"],
                                        )          
                inbound_data_list.append(inbound_data)

        return inbound_data_list

    def quit_session(self) -> None:
        self._opener.close()
        self._refresh_task.cancel()

    def validate_cookie(self) -> bool:
        return self._get_xcsrf()

    @property
    def value_list(self):
        return self._value_list