"""
Windows Notification Manager
Отправляет системные уведомления через Windows API
"""

import logging
import ctypes
import platform
from typing import Optional

logger = logging.getLogger(__name__)


class WindowsNotification:
    """Менеджер системных уведомлений Windows"""
    
    def __init__(self, app_name: str = "FocusPilot"):
        self.app_name = app_name
        self.is_windows = platform.system() == "Windows"
        
    def send_notification(self, title: str, message: str, duration: int = 5000) -> bool:
        """
        Отправить системное уведомление Windows
        
        Args:
            title: заголовок уведомления
            message: текст уведомления
            duration: длительность показа в миллисекундах (по умолчанию 5000)
            
        Returns:
            True если уведомление отправлено успешно
        """
        try:
            if self.is_windows:
                return self._send_windows_notification(title, message, duration)
            else:
                return self._send_fallback_notification(title, message)
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False
    
    def _send_windows_notification(self, title: str, message: str, duration: int = 5000) -> bool:
        """Отправить уведомление через Windows API (Shell_NotifyIcon)"""
        try:
            import ctypes.wintypes
            
            class NOTIFYICONDATA(ctypes.Structure):
                _fields_ = [
                    ("cbSize", ctypes.wintypes.DWORD),
                    ("hWnd", ctypes.wintypes.HWND),
                    ("uID", ctypes.wintypes.UINT),
                    ("uFlags", ctypes.wintypes.UINT),
                    ("uCallbackMessage", ctypes.wintypes.UINT),
                    ("hIcon", ctypes.wintypes.HICON),
                    ("szTip", ctypes.c_wchar * 128),
                    ("dwState", ctypes.wintypes.DWORD),
                    ("dwStateMask", ctypes.wintypes.DWORD),
                    ("szInfo", ctypes.c_wchar * 256),
                    ("uTimeout", ctypes.wintypes.UINT),
                    ("szInfoTitle", ctypes.c_wchar * 64),
                    ("dwInfoFlags", ctypes.wintypes.DWORD),
                    ("guidItem", ctypes.c_char * 16),
                    ("hBalloonIcon", ctypes.wintypes.HICON),
                ]
            
            NIF_INFO = 0x00000010
            NIIF_INFO = 0x00000001
            NIM_ADD = 0x00000000
            NIM_DELETE = 0x00000002
            
            shell32 = ctypes.windll.shell32
            user32 = ctypes.windll.user32
            
            class_name = ctypes.c_wchar_p("FocusPilotNotify")
            wc = ctypes.wintypes.WNDCLASSEXW()
            wc.cbSize = ctypes.sizeof(wc)
            wc.lpfnWndProc = ctypes.wintypes.WNDPROC(user32.DefWindowProcW)
            wc.hInstance = ctypes.windll.kernel32.GetModuleHandleW(None)
            wc.lpszClassName = class_name
            
            atom = user32.RegisterClassExW(ctypes.byref(wc))
            hwnd = user32.CreateWindowExW(
                0, class_name, "FocusPilot", 0, 0, 0, 0, 0,
                None, None, wc.hInstance, None
            )
            
            nid = NOTIFYICONDATA()
            nid.cbSize = ctypes.sizeof(nid)
            nid.hWnd = hwnd
            nid.uID = 1
            nid.uFlags = NIF_INFO
            nid.dwInfoFlags = NIIF_INFO
            nid.uTimeout = duration
            nid.szInfoTitle = title[:63]
            nid.szInfo = message[:255]
            nid.szTip = self.app_name[:127]
            
            result = shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid))
            if result:
                logger.info(f"Windows notification sent: {title}")
                import threading
                def cleanup():
                    import time
                    time.sleep(5)
                    shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(nid))
                    user32.DestroyWindow(hwnd)
                threading.Thread(target=cleanup, daemon=True).start()
                return True
            else:
                raise Exception("Shell_NotifyIcon failed")
                
        except Exception as e:
            logger.debug(f"Windows API notification failed: {e}, trying fallback...")
            return self._send_fallback_notification(title, message)
    
    def _send_fallback_notification(self, title: str, message: str) -> bool:
        """Fallback: показать уведомление через print"""
        try:
            print(f"NOTIFICATION: {title} - {message}")
            logger.info(f"Fallback notification: {title}")
            return True
        except Exception as e:
            logger.error(f"Fallback notification failed: {e}")
            return False
    
    def send_distraction_alert(self, app_name: str = "unknown", duration_minutes: float = 0) -> bool:
        """
        Отправить специальное уведомление об отвлечении
        
        Args:
            app_name: название приложения-отвлечения
            duration_minutes: длительность отвлечения в минутах
            
        Returns:
            True если уведомление отправлено
        """
        title = "FocusPilot: Distraction Detected!"
        message = f"You have been distracted for {duration_minutes:.0f} min in '{app_name}'. Return to work!"
        return self.send_notification(title, message)
    
    def send_warning_alert(self, probability: float, app_name: str = "unknown") -> bool:
        """
        Отправить предупреждение о возможном отвлечении
        
        Args:
            probability: вероятность отвлечения (0.0-1.0)
            app_name: текущее приложение
            
        Returns:
            True если уведомление отправлено
        """
        title = "FocusPilot: Warning!"
        message = f"Distraction probability: {probability*100:.0f}%. Focus on your task!"
        return self.send_notification(title, message)
    
    def send_motivational_message(self) -> bool:
        """Отправить мотивационное сообщение"""
        import random
        messages = [
            "Great work! Keep it up!",
            "You are productive! Stay focused!",
            "Focus is the key to success!",
            "You are on the right track!",
            "Time for productive work!",
        ]
        message = random.choice(messages)
        return self.send_notification("FocusPilot: Motivation", message)