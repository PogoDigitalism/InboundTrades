import time
import sys
import asyncio
from concurrent.futures import ThreadPoolExecutor

from log_comms import Log, LogAction
from ui import SubmitDataApp
from data import DataManager
from utils import SyncInAsync
from win_comms import ToastManager
from http_comms import HttpManager

INBOUND_COOLDOWN = 5
TOAST_DISPLAY_TIME = 6

class Handler:
    def __init__(self) -> None:
        self._toast_queue = list()
        # DATA INITIALIZATION
        self.data_manager = DataManager()

        data_present = self.data_manager.validate_data()
        if not data_present:
            # Initiate UI booter for empty data:  
            self.submit_data_app = SubmitDataApp("No data found, submit your .ROBLOSECURITY below to start receiving inbound trades.")
            saved = self.submit_data_app.enable_app()

            if not saved:
                sys.exit()

        pool = ThreadPoolExecutor()
        self._loop = asyncio.get_event_loop()

        self.toast_manager = ToastManager()
        self.sync_in_async = SyncInAsync(POOL=pool)
        self.http_manager = HttpManager()

        self._validate_cookie()
        self.http_manager.initialize_session()

        Log.info("Initialized Handler")

    def _validate_cookie(self):
        is_success = self.http_manager.validate_cookie()
        if not is_success:
            # Initiate UI booter for invalid data:  
            self.submit_data_app = SubmitDataApp("Invalid cookie, submit your .ROBLOSECURITY below to start receiving inbound trades.")
            saved = self.submit_data_app.enable_app()

            #recursion to check for a valid cookie again.
            if saved:
                return self._validate_cookie()
        else:
            Log.info("Validated cookie")

    async def _handle_toast(self):
        while True:
            if self._toast_queue:
                inbound = self._toast_queue[0]          
                self.toast_manager.create_toast(message=f"{inbound.username} | Trade inbound", title="")
                del self._toast_queue[0]

                await asyncio.sleep(TOAST_DISPLAY_TIME)
                self.toast_manager.delete_toast()

    async def check_inbounds(self):
        self._loop.create_task(self._handle_toast())
        while True:
            inbound_data = await self.http_manager.check_inbound_trades()
            self._toast_queue.extend(inbound_data)

            await asyncio.sleep(INBOUND_COOLDOWN)

async def run():
    handler = Handler()
    await handler.check_inbounds()