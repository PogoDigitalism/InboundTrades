import time
import sys
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ui.submit_data import SubmitDataApp
from data.data_manager import DataManager
from utils.syncinasync import SyncInAsync
from win_comms.toast_manager import ToastManager
from http_comms.http_manager import HttpManager

class Handler:
    def __init__(self) -> None:
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
        loop = asyncio.get_event_loop()

        self.toast_manager = ToastManager()
        self.sync_in_async = SyncInAsync(POOL=pool)
        self.http_manager = HttpManager()

        self._validate()

    def _validate(self):
        is_success = self.http_manager.validate_cookie()
        if not is_success:
            # Initiate UI booter for invalid data:  
            self.submit_data_app = SubmitDataApp("Invalid cookie, submit your .ROBLOSECURITY below to start receiving inbound trades.")
            saved = self.submit_data_app.enable_app()

            #recursion to check for a valid cookie again.
            if saved:
                return self._validate()

    async def _handle_toast(self):
        pass

    async def check_inbounds(self):
        while True:
            self.toast_manager.create_toast("test", "big test")

            await asyncio.sleep(5)
            self.toast_manager.delete_toast()

async def run():
    handler = Handler()
    await handler.check_inbounds()