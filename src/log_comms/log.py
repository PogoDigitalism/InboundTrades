import logging
import datetime
import asyncio
import typing

import urllib.error as error

# MESSAGE CODES
NO_DATA_FOUND = 10
DATA_FOUND = 11

VALIDATION_FAIL = 20
VALIDATION_SUCCESS = 21

XCSRF_FAIL = 30
XCSRF_SUCCESS = 31

INBOUND_FAIL = 40
INBOUND_SUCCESS = 41



# class ColoredFormatter(logging.Formatter):
#     WARNING = '\x1b[33m'
#     ERROR = '\x1b[1;31m'
#     CRITICAL = '\x1b[31m'
#     RESET = '\x1b[0m'
#     SUCCESS = '\x1b[1;32m'

#     def format(self, record):
#         log_time = datetime.datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")

#         level_color = getattr(self, record.levelname, '')
#         message = super().format(record)

#         return f"{log_time} {level_color} [{record.levelname}] {self.COLORS['RESET']} {message}"

class ColoredFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    FORMATS = {
        logging.DEBUG: f"%(asctime)s - %(name)s - %(levelname)s - {grey} %(message)s {reset}",
        logging.INFO: f"%(asctime)s - %(name)s - %(levelname)s - {grey} %(message)s {reset}",
        logging.WARNING: f"%(asctime)s - %(name)s - %(levelname)s - {yellow} %(message)s {reset}",
        logging.ERROR: f"%(asctime)s - %(name)s - %(levelname)s - {red} %(message)s {reset}",
        logging.CRITICAL: f"%(asctime)s - %(name)s - %(levelname)s - {bold_red} %(message)s {reset}"
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

cf = ColoredFormatter()

# REGULAR MSG LOGGING
msg_logger = logging.getLogger("MSG_LOG")
msg_logger.setLevel(logging.INFO)

msg_file_handler = logging.FileHandler("src/log_comms/logs/logs.txt")
msg_file_handler.setFormatter(cf)
msg_logger.addHandler(msg_file_handler)

msg_stream_handler = logging.StreamHandler()
msg_stream_handler.setFormatter(cf)
msg_logger.addHandler(msg_stream_handler)

# EXCEPTION LOGGING
exception_logger = logging.getLogger("EXCEPTION_LOG")
exception_logger.setLevel(logging.ERROR)

exception_file_handler = logging.FileHandler("src/log_comms/logs/exception_logs.txt")
exception_file_handler.setFormatter(cf)
exception_logger.addHandler(exception_file_handler)

exception_stream_handler = logging.StreamHandler()
exception_stream_handler.setFormatter(cf)
exception_logger.addHandler(exception_stream_handler)


class Log:
    @staticmethod
    def info(msg):
        msg_logger.info(msg)

    @staticmethod
    def warning(msg):
        msg_logger.warning(msg)

    @staticmethod
    def error(msg):
        exception_logger.error(msg)

    @staticmethod
    def critical(msg):
        exception_logger.critical(msg)

    @staticmethod
    def debug(msg):
        msg_logger.debug(msg)

    @staticmethod
    def exception(msg):
        exception_logger.exception(msg)

    @staticmethod
    def wrap_http(func: typing.Callable, request_struct , success_codes: list[int], *args, **kwargs) -> typing.Any:
        try:
            resp = func(request_struct, *args, **kwargs)

            Log.info(f"Opened URL: {request_struct.get_method()} {resp.url} with code {resp.code}")

            return resp
        except error.HTTPError as resp:
            if resp.code not in success_codes:
                Log.error(f"HTTPError for {request_struct.get_method()} {resp.url}: [{resp.code}] | {resp.read()}")
            else:
                Log.info(f"Opened URL: {request_struct.get_method()} {resp.url} with code {resp.code}")
            raise resp

    @staticmethod
    def wrap_generic(func: typing.Callable, *args, **kwargs) -> typing.Any:
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            Log.error(f'{e}')
            raise e

# -> @LogActions
def LogAction(func):
    def _parse_code(code: int):
        ...

    def _log_parsed(msg: str, levelname: str):
        getattr(Log, levelname)(msg)

    async def awrapper(*args, **kwargs):
        log_code = None
        # some logic here
        result = await func(_log_code=log_code, *args, **kwargs)
        return result
    
    def wrapper(*args, **kwargs):
        log_code = None
        # some logic here
        result = func(_log_code=log_code, *args, **kwargs)
        print(func._log_code)
        return result

    if asyncio.iscoroutine(func):
        return awrapper
    else:
        return wrapper
