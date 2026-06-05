"""
Tray Icon
Трей иконка приложения с быстрыми уведомлениями
"""

import logging
from typing import Optional, Callable, Dict, Any
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw
import os

logger = logging.getLogger(__name__)


class TrayIconManager:
    """Менеджер трей иконки"""
    
    def __init__(self, on_quit: Optional[Callable] = None):
        """
        Инициализация трей иконки
        
        Args:
            on_quit: функция при выходе
        """
        self.on_quit = on_quit or (lambda: None)
        self.icon = None
        self.is_running = False
        
        # Создаем иконку
        self._create_icon()
    
    def _create_icon(self) -> None:
        """Создание иконки приложения"""
        # Создаем простую иконку (синий квадрат с буквой F)
        image = Image.new('RGB', (64, 64), color=(40, 120, 200))
        draw = ImageDraw.Draw(image)
        
        # Рисуем букву F
        draw.text((20, 15), "F", fill=(255, 255, 255))
        
        menu = Menu(
            MenuItem('Show', self._on_show),
            MenuItem('Settings', self._on_settings),
            MenuItem('Start Monitoring', self._on_start),
            MenuItem('Stop Monitoring', self._on_stop),
            MenuItem('-'),
            MenuItem('Quit', self._on_quit_clicked)
        )
        
        self.icon = Icon("focuspilot", image, menu=menu)
    
    def run(self) -> None:
        """Запуск трей иконки"""
        if self.icon:
            try:
                self.is_running = True
                self.icon.run()
            except Exception as e:
                logger.error(f"Error running tray icon: {e}")
                self.is_running = False
    
    def stop(self) -> None:
        """Остановка трей иконки"""
        if self.icon:
            self.icon.stop()
            self.is_running = False
    
    def show_notification(
        self,
        title: str,
        message: str,
        notification_type: str = "info"
    ) -> None:
        """
        Показать уведомление
        
        Args:
            title: заголовок
            message: сообщение
            notification_type: тип уведомления (info, warning, error)
        """
        if self.icon:
            try:
                # pystray использует встроенные уведомления ОС
                self.icon.notify(message, title)
            except Exception as e:
                logger.debug(f"Could not show notification: {e}")
    
    def update_tooltip(self, text: str) -> None:
        """
        Обновить подсказку иконки
        
        Args:
            text: текст подсказки
        """
        if self.icon:
            try:
                self.icon.title = text[:64]  # ограничение длины
            except Exception as e:
                logger.debug(f"Could not update tooltip: {e}")
    
    def _on_show(self, icon, item):
        """Показать главное окно"""
        logger.info("Show window")
    
    def _on_settings(self, icon, item):
        """Открыть настройки"""
        logger.info("Open settings")
    
    def _on_start(self, icon, item):
        """Запустить мониторинг"""
        logger.info("Start monitoring")
    
    def _on_stop(self, icon, item):
        """Остановить мониторинг"""
        logger.info("Stop monitoring")
    
    def _on_quit_clicked(self, icon, item):
        """Выход"""
        logger.info("Quit requested")
        self.on_quit()
        self.stop()
