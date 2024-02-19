import time
import sys
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ui.submit_data import SubmitDataApp
from data.data_manager import DataManager
from utils.syncinasync import SyncInAsync
from win_comms.toast_managener import ToastManager
from http_comms.http_manager import HttpManager

class Handler:
    async def __init__(self) -> None:
        # DATA INITIALIZATION
        self.data_manager = DataManager()

        data_present = self.data_manager.validate_data()
        if not data_present:
            # Initiate UI booter for empty data:  
            self.submit_data_app = SubmitDataApp("No data found, submit your .ROBLOSECURITY below to start receiving inbound trades.")
            self.submit_data_app.enable_app()

            #clean-up
            self.submit_data_app.destroy()

        # 
        pool = ThreadPoolExecutor()

        self.toast_manager = ToastManager()
        self.sync_in_async = SyncInAsync(POOL=pool)
        self.http_manager = HttpManager()

        self._validate()

    def _validate(self):
        is_success = self.http_manager.validate_cookie()
        if not is_success:
            # Initiate UI booter for invalid data:  
            self.submit_data_app = SubmitDataApp("Invalid cookie, submit your .ROBLOSECURITY below to start receiving inbound trades.")
            self.submit_data_app.enable_app()

            #clean-up
            self.submit_data_app.destroy()

            #recursion to check for a valid cookie again.
            return self._validate()


    async def _handle_toast(self):
        pass




async def run():
    handler = Handler()