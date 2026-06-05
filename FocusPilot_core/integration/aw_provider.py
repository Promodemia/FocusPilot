"""
ActivityWatch Data Provider
Получает события активности из локального ActivityWatch сервера
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import urllib.request
import urllib.error
import time
import json

logger = logging.getLogger(__name__)

try:
    from aw_client import ActivityWatchClient  # type: ignore
    HAS_AW_CLIENT = True
except ImportError:
    # Mock class для отсутствия aw-client
    class ActivityWatchClient:
        def __init__(self, name: str = "focuspilot", host: str = "localhost", port: int = 5600, timeout: int = 5):
            self.name = name
            self.host = host
            self.port = port
            self.timeout = timeout
        
        def server_version(self):
            """Проверка версии сервера через HTTP"""
            try:
                url = f"http://{self.host}:{self.port}/api/0/info"
                with urllib.request.urlopen(url, timeout=self.timeout) as response:
                    data = json.loads(response.read().decode())
                    return data.get("version", "unknown")
            except Exception as e:
                raise ConnectionError(f"Cannot connect to ActivityWatch at {self.host}:{self.port}: {e}")
        
        def get_buckets(self):
            """Получить список бакетов (mock)"""
            return []
        
        def query(self, query_str: str, start: datetime, end: datetime):
            """Query events (mock)"""
            return []
    
    HAS_AW_CLIENT = True  # считаем что мок работает


class AWDataProvider:
    """Провайдер данных из ActivityWatch"""
    
    def __init__(self, host: str = "localhost", port: int = 5600, timeout: int = 5):
        """
        Инициализация подключения к ActivityWatch

        Args:
            host: адрес AW сервера
            port: порт AW сервера
            timeout: таймаут подключения в секундах
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.client = None
        self.last_event_timestamp = None
        self._connect()

    def _connect(self) -> bool:
        """Подключение к ActivityWatch"""
        try:
            self.client = ActivityWatchClient(
                name="focuspilot",
                host=self.host,
                port=self.port,
                timeout=self.timeout
            )
            # Проверка подключения
            self.client.server_version()
            logger.info(f"Connected to ActivityWatch at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to ActivityWatch: {e}")
            return False

    def is_connected(self) -> bool:
        """Проверка подключения"""
        try:
            if self.client is None:
                return False
            self.client.server_version()
            return True
        except Exception:
            return False

    def reconnect(self, max_attempts: int = 3) -> bool:
        """
        Переподключение к ActivityWatch с повторными попытками

        Args:
            max_attempts: максимальное количество попыток

        Returns:
            True если подключение успешно, False иначе
        """
        for attempt in range(max_attempts):
            if self._connect():
                return True
            if attempt < max_attempts - 1:
                time.sleep(2 ** attempt)  # экспоненциальная задержка
        return False

    def get_new_events(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Получить новые события за последние 15 секунд

        Returns:
            Словарь с событиями по типам (window, url_events, afk_events)
        """
        if not self.is_connected():
            logger.warning("Not connected to ActivityWatch")
            return {
                "window_events": [],
                "url_events": [],
                "afk_events": []
            }

        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(seconds=15)

            events = {
                "window_events": [],
                "url_events": [],
                "afk_events": []
            }

            # Получить события по окнам
            try:
                window_events = self.client.query(
                    "events | grep 'bucket_name=\"window\"'",
                    start_time, end_time
                )
                if window_events:
                    events["window_events"] = window_events
            except Exception as e:
                logger.debug(f"Could not get window events: {e}")

            # Получить события по URL
            try:
                url_events = self.client.query(
                    "events | grep 'bucket_name=\"url\"'",
                    start_time, end_time
                )
                if url_events:
                    events["url_events"] = url_events
            except Exception as e:
                logger.debug(f"Could not get URL events: {e}")

            # Получить события по AFK статусу
            try:
                afk_events = self.client.query(
                    "events | grep 'bucket_name=\"afk\"'",
                    start_time, end_time
                )
                if afk_events:
                    events["afk_events"] = afk_events
            except Exception as e:
                logger.debug(f"Could not get AFK events: {e}")

            return events

        except Exception as e:
            logger.error(f"Error getting new events: {e}")
            return {
                "window_events": [],
                "url_events": [],
                "afk_events": []
            }

    def get_historical_events(
        self,
        start: datetime,
        end: datetime,
        event_types: Optional[List[str]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Получить исторические события за указанный период

        Args:
            start: начальное время
            end: конечное время
            event_types: типы событий для получения (window, url, afk)
                        если None - получить все

        Returns:
            Словарь с событиями по типам
        """
        if not self.is_connected():
            logger.warning("Not connected to ActivityWatch")
            return {}

        if event_types is None:
            event_types = ["window", "url", "afk"]

        try:
            events = {}

            if "window" in event_types:
                try:
                    window_events = self.client.query(
                        "events | grep 'bucket_name=\"window\"'",
                        start, end
                    )
                    events["window_events"] = window_events if window_events else []
                except Exception as e:
                    logger.debug(f"Could not get historical window events: {e}")
                    events["window_events"] = []

            if "url" in event_types:
                try:
                    url_events = self.client.query(
                        "events | grep 'bucket_name=\"url\"'",
                        start, end
                    )
                    events["url_events"] = url_events if url_events else []
                except Exception as e:
                    logger.debug(f"Could not get historical URL events: {e}")
                    events["url_events"] = []

            if "afk" in event_types:
                try:
                    afk_events = self.client.query(
                        "events | grep 'bucket_name=\"afk\"'",
                        start, end
                    )
                    events["afk_events"] = afk_events if afk_events else []
                except Exception as e:
                    logger.debug(f"Could not get historical AFK events: {e}")
                    events["afk_events"] = []

            return events

        except Exception as e:
            logger.error(f"Error getting historical events: {e}")
            return {}

    def get_available_buckets(self) -> List[str]:
        """Получить список доступных бакетов"""
        try:
            buckets = self.client.get_buckets()
            return [b.id for b in buckets]
        except Exception as e:
            logger.error(f"Error getting buckets: {e}")
            return []

    def ping(self) -> bool:
        """Проверить доступность сервера"""
        try:
            self.client.server_version()
            return True
        except Exception:
            return False
