########## WIN32 API COMMUNICATION
# Useful links:
## Shell_NotifyIconW function: https://learn.microsoft.com/en-us/windows/win32/api/shellapi/nf-shellapi-shell_notifyiconw
## NOTIFYICONDATAW structure: https://learn.microsoft.com/en-us/windows/win32/api/shellapi/ns-shellapi-notifyicondataw

import threading
import asyncio
import webbrowser
import typing
import time
import ctypes
from ctypes import wintypes

import exceptions

# Application messages
WM_USER = 0x0400
WM_TOAST_CLICKED = WM_USER + 1


# Shell_NotifyIconW identifiers
NIM_ADD = 0x00000000
NIM_MODIFY = 0x00000001
NIM_DELETE = 0x00000002


# NOTIFYICONDATA Struct identifiers
NIF_MESSAGE = 0x00000001
NIF_ICON = 0x00000002
NIF_TIP = 0x00000004
NIF_INFO = 0x00000010
NIF_SHOWTIP = 0x00000080

## dwState(Mask)
NIS_HIDDEN = 0x00000001
NIS_SHAREDICON = 0x00000002


# LoadImageW identifiers
LR_LOADFROMFILE = 0x00000010
LR_CREATEDIBSECTION = 0x00002000

WNDPROC = ctypes.WINFUNCTYPE(
    wintypes.LPARAM, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM
)

# Window class structure
class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", wintypes.HANDLE),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
    ]

class _NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hWnd", wintypes.HWND),
        ("uID", wintypes.UINT), # icon identifier
        ("uFlags", wintypes.UINT),
        ("uCallbackMessage", wintypes.UINT),
        ("hIcon", wintypes.HICON),
        ("szTip", wintypes.WCHAR * 128),
        ("dwState", wintypes.DWORD),
        ("dwStateMask", wintypes.DWORD),
        ("szInfo", wintypes.WCHAR * 256),
        ("szInfoTitle", wintypes.WCHAR * 64),
        ("dwInfoFlags", wintypes.DWORD),
        ("guidItem", wintypes.UINT),
    ]

class ToastManager:
    """
    Proud of this one.
    """
    def __init__(self) -> None:
        self.shell32 = ctypes.windll.shell32
        self.user32 = ctypes.windll.user32

    def initialize_window_handler(self):
        self._create_window()
        self._message_loop()

    def create_toast(self, message: str, title: str, icon_path=None):
        ### Shout-out to Windows for making their massive Win32 api documentation extensive and nice to read
        ### Dm me on Discord (PogoDigitalism) if you need help to understand whats going on


        # instance NOTIFYICONDATAW struct
        self.NID_struct: ctypes.Structure = _NOTIFYICONDATAW()

        self.NID_struct.cbSize = ctypes.sizeof(self.NID_struct) # UINT representing byte size

        self.NID_struct.hWnd = self.hwnd #UINT
        
        self.NID_struct.uID = 0 #UINT

        # use bitwise OR "|" operator for proper flag manipulation
        self.NID_struct.uFlags = NIF_TIP | NIF_INFO | NIF_SHOWTIP | NIF_MESSAGE # UINT

        # uCallbackMessage for Window class
        self.NID_struct.uCallbackMessage = WM_TOAST_CLICKED # UINT

        self.NID_struct.hIcon = self.__load_icon(icon_path) if icon_path else 0
  
        self.NID_struct.szTip = message # WCHAR

        # icon state
        ## No need to hide, so we'll keep this commented out
        # self.NID_struct.dwState = NIS_HIDDEN

        self.NID_struct.szInfo = message # WCHAR

        self.NID_struct.szInfoTitle = title # WCHAR

        # display icon to the status area
        toast = self.shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(self.NID_struct))
        if not toast:
            toast = self.shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(self.NID_struct))
            # raise exceptions.InvalidToastException(f"Toast with identifier {self.NID_struct.uID} was either not deleted, has invalid members or has invalid struct types")

    def delete_toast(self):
        self.shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(self.NID_struct))
        # self.user32.DestroyWindow(self.hwnd) # commented out as we need only one Window handler for all new toast notifications
        # self.user32.UnregisterClassW('RobloxRedirect', None)

    def _window_procedure(self, hwnd, msg, wparam, lparam):
        print(hwnd, msg, wparam, lparam)
        if msg == WM_TOAST_CLICKED and lparam == 1029: # validates that the Window message is the correct message type. Also checks for lparam 1029. 1029 means that the notification was clicked.
            webbrowser.open('https://roblox.com/trades')
        return self.user32.DefWindowProcW(hwnd, msg, wparam, ctypes.c_int64(lparam)) # message processing satisfyer

    def _create_window(self):
        self.wnd_class = WNDCLASSW()
        self.wnd_class.lpfnWndProc = WNDPROC(self._window_procedure) # set
        self.wnd_class.lpszClassName = 'RobloxRedirect'

        self.user32.RegisterClassW(ctypes.byref(self.wnd_class))

        self.hwnd = self.user32.CreateWindowExW(
            0,
            'RobloxRedirect',
            'BrowserWindow',
            0,
            0, 0, 0, 0,
            None,
            None,
            None,
            None
        )

    def _message_loop(self):
        msg = wintypes.MSG()
        while self.user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            self.user32.TranslateMessage(ctypes.byref(msg))
            self.user32.DispatchMessageW(ctypes.byref(msg))

    @staticmethod
    def __load_icon(
        icon_path,
        icon_type=1,
        cx_desired=32,
        cy_desired=32,
        load_flags=LR_LOADFROMFILE | LR_CREATEDIBSECTION,
    ):
        user32 = ctypes.windll.user32
        LoadImageW = user32.LoadImageW
        LoadImageW.restype = (
            ctypes.c_void_p
        )
        LoadImageW.argtypes = [
            wintypes.HINSTANCE,
            wintypes.LPCWSTR,
            wintypes.UINT,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.UINT,
        ]

        icon = LoadImageW(None, icon_path, icon_type, cx_desired, cy_desired, load_flags)
        if not icon:
            raise IOError("Failed to load icon from file")

        return icon

    @property
    def NOTIFYICONDATAW(self):
        return self.NID_struct
    
    @NOTIFYICONDATAW.setter
    def NOTIFYICONDATAW(self, NOTIFYICONDATAW_members: dict[str, typing.Any]):
        """
        NOTIFYICONDATAW_members may only contain verified NOTIFYICONDATAW structure members. The toast will not work if otherwise.
        """
        for member, value in NOTIFYICONDATAW_members.items():
            setattr(self.NID_struct, member, value)

__all__ = ["ToastManager"]
