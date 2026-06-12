import asyncio
import logging
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json
import platform

try:
    from aw_client import ActivityWatchClient
    HAS_AW = True
except ImportError:
    HAS_AW = False

logger = logging.getLogger(__name__)


def get_active_window_windows() -> Dict[str, str]:
    """Получить активное окно через Windows API"""
    try:
        import ctypes
        from ctypes import wintypes
        
        user32 = ctypes.windll.user32
        
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return {"app_name": "unknown", "window_title": ""}
        
        length = user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return {"app_name": "unknown", "window_title": ""}
        
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        window_title = buf.value
        
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(0x0400 | 0x0010, False, pid.value)
        if handle:
            buf = ctypes.create_unicode_buffer(512)
            kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(ctypes.c_ulong(512)))
            process_path = buf.value
            app_name = process_path.split("\\")[-1].replace(".exe", "") if process_path else "unknown"
            kernel32.CloseHandle(handle)
        else:
            app_name = "unknown"
        
        return {"app_name": app_name, "window_title": window_title}
    except Exception as e:
        logger.debug(f"Error getting active window: {e}")
        return {"app_name": "unknown", "window_title": ""}


class ActivityWatchMonitor:
    def __init__(self, ml_model):
        self.ml_model = ml_model
        self.aw_client = None
        self.is_monitoring = False
        self.is_paused = False
        self.current_category = "unknown"
        self.distraction_start = None
        self.category_history = []
        self.daily_stats = {
            "work": 0,
            "communication": 0,
            "distraction": 0,
            "break": 0,
            "unknown": 0
        }
        
        if HAS_AW:
            try:
                self.aw_client = ActivityWatchClient("focuspilot")
                self.aw_client.get_info()
                logger.info("Connected to ActivityWatch")
            except Exception as e:
                logger.error(f"Failed to connect to AW: {e}")
                self.aw_client = None

    def is_available(self) -> bool:
        """Check if AW is available"""
        if not HAS_AW or not self.aw_client:
            return False
        try:
            self.aw_client.get_info()
            return True
        except:
            return False

    def get_current_activity(self) -> Dict[str, Any]:
        """Get current activity from AW or Windows API fallback"""
        app_name = "unknown"
        window_title = ""
        
        # Try ActivityWatch first
        if self.aw_client:
            try:
                end = datetime.utcnow()
                start = end - timedelta(seconds=15)
                
                events = self.aw_client.query(
                    'events | grep "bucket_name=\\"window\\""',
                    start, end
                )
                
                if events:
                    latest = events[-1]
                    app_name = latest.get("data", {}).get("app", "unknown")
                    window_title = latest.get("data", {}).get("title", "")
            except Exception as e:
                logger.debug(f"Error querying AW: {e}")
        
        # Fallback to Windows API if AW unavailable
        if app_name == "unknown":
            aw_result = get_active_window_windows()
            app_name = aw_result["app_name"]
            window_title = aw_result["window_title"]
        
        # Classify activity using ML model
        category, confidence = self.ml_model.classify(app_name, {})
        
        return {
            "app_name": app_name,
            "window_title": window_title,
            "category": category,
            "confidence": confidence
        }

    async def monitor_loop(self, notify_callback):
        """Main monitoring loop - runs every 2 seconds"""
        self.is_monitoring = True
        
        while self.is_monitoring:
            try:
                # Skip processing if paused
                if self.is_paused:
                    await asyncio.sleep(2)
                    continue
                
                activity = self.get_current_activity()
                category = activity["category"]
                
                if category != self.current_category:
                    self.current_category = category
                    self.distraction_start = None
                
                self.category_history.append(category)
                if len(self.category_history) > 100:
                    self.category_history.pop(0)
                
                # Update stats
                if category in self.daily_stats:
                    self.daily_stats[category] += 2  # 2 seconds
                
                # Check for distraction
                if category == "distraction":
                    if self.distraction_start is None:
                        self.distraction_start = datetime.utcnow()
                    else:
                        duration = (datetime.utcnow() - self.distraction_start).total_seconds() / 60
                        if duration >= 2:  # 2 minutes
                            await notify_callback({
                                "title": "FocusPilot: Distraction Alert",
                                "message": f"Distracted for {duration:.0f} minutes",
                                "category": category,
                                "app": activity.get("app_name", "unknown")
                            })
                            self.distraction_start = datetime.utcnow()
                else:
                    self.distraction_start = None
                
                # Check ML prediction
                distraction_prob = self.ml_model.predict_distraction(self.category_history)
                if distraction_prob > 0.7 and category != "distraction":
                    await notify_callback({
                        "title": "FocusPilot: Potential Distraction",
                        "message": f"Distraction probability: {distraction_prob*100:.0f}%",
                        "category": category,
                        "app": activity.get("app_name", "unknown")
                    })
                
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                await asyncio.sleep(2)

    def stop_monitoring(self):
        """Stop monitoring"""
        self.is_monitoring = False

    def pause_monitoring(self):
        """Pause monitoring without stopping the loop"""
        self.is_paused = True

    def resume_monitoring(self):
        """Resume monitoring"""
        self.is_paused = False

    def get_stats(self) -> Dict[str, int]:
        """Get current session stats"""
        return self.daily_stats.copy()
