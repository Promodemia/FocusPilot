"""
Notifications
Система уведомлений с кнопками действий
"""

import logging
from typing import Dict, Any, Callable, Optional
from datetime import datetime
from plyer import notification as plyer_notification
import threading

logger = logging.getLogger(__name__)


class NotificationManager:
    """Менеджер уведомлений"""
    
    def __init__(self, tray_icon=None):
        """
        Инициализация менеджера уведомлений
        
        Args:
            tray_icon: экземпляр трей иконки для показа уведомлений
        """
        self.tray_icon = tray_icon
        self.notification_handlers = {}
        self.last_notification_time = None
        self.notification_cooldown = 120  # минимум 2 минуты между уведомлениями
    
    def register_handler(self, notification_type: str, handler: Callable) -> None:
        """
        Регистрация обработчика уведомления
        
        Args:
            notification_type: тип уведомления
            handler: функция-обработчик
        """
        self.notification_handlers[notification_type] = handler
    
    def show_distraction_alert(
        self,
        category: str,
        probability: float,
        duration: float,
        features: Dict[str, Any]
    ) -> None:
        """
        Показать уведомление об отвлечении
        
        Args:
            category: категория активности
            probability: вероятность отвлечения
            duration: длительность в минутах
            features: признаки активности
        """
        # Проверяем cooldown
        if self.last_notification_time:
            time_since_last = datetime.utcnow() - self.last_notification_time
            if time_since_last.total_seconds() < self.notification_cooldown:
                logger.debug("Notification cooldown active")
                return
        
        title = "Distraction Detected"
        message = (
            f"You've been {category} for {duration:.0f} minutes.\n"
            f"Confidence: {probability*100:.0f}%\n\n"
            f"App: {features.get('app_name', 'Unknown')}\n"
            f"Would you like to return to work?"
        )
        
        self._show_notification(
            title=title,
            message=message,
            notification_type="distraction",
            data={
                "category": category,
                "probability": probability,
                "features": features,
            }
        )
    
    def show_break_reminder(self) -> None:
        """Показать напоминание о перерыве"""
        title = "Break Time"
        message = "You've been working for a while. Time for a break?"
        
        self._show_notification(
            title=title,
            message=message,
            notification_type="break_reminder"
        )
    
    def show_plan_check(self, current_activity: str, planned_activity: str) -> None:
        """
        Показать проверку соответствия с планом
        
        Args:
            current_activity: текущая активность
            planned_activity: плановая активность
        """
        title = "Plan Mismatch"
        message = (
            f"Currently doing: {current_activity}\n"
            f"According to plan: {planned_activity}\n\n"
            f"Is this correct?"
        )
        
        self._show_notification(
            title=title,
            message=message,
            notification_type="plan_check"
        )
    
    def show_stats_summary(self, stats: Dict[str, Any]) -> None:
        """
        Показать сводку статистики
        
        Args:
            stats: словарь со статистикой
        """
        work_hours = stats.get('work_time', 0) / 3600
        distraction_hours = stats.get('distraction_time', 0) / 3600
        
        title = "Daily Summary"
        message = (
            f"Work: {work_hours:.1f}h\n"
            f"Distractions: {distraction_hours:.1f}h\n"
            f"Plan adherence: {stats.get('plan_adherence', 0)*100:.0f}%"
        )
        
        self._show_notification(
            title=title,
            message=message,
            notification_type="stats_summary"
        )
    
    def _show_notification(
        self,
        title: str,
        message: str,
        notification_type: str,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Показать уведомление
        
        Args:
            title: заголовок
            message: сообщение
            notification_type: тип уведомления
            data: дополнительные данные
        """
        self.last_notification_time = datetime.utcnow()
        
        # Показываем через системное уведомление
        try:
            plyer_notification.notify(
                title=title,
                message=message,
                app_name="FocusPilot",
                timeout=10
            )
            logger.info(f"Notification shown: {notification_type}")
        except Exception as e:
            logger.debug(f"Could not show system notification: {e}")
        
        # Показываем через трей иконку
        if self.tray_icon:
            self.tray_icon.show_notification(title, message)
        
        # Вызываем зарегистрированный обработчик
        if notification_type in self.notification_handlers:
            handler = self.notification_handlers[notification_type]
            threading.Thread(target=handler, args=(data or {},)).start()
    
    def handle_notification_action(
        self,
        notification_type: str,
        action: str,
        data: Dict[str, Any]
    ) -> None:
        """
        Обработка действия пользователя на уведомлении
        
        Args:
            notification_type: тип уведомления
            action: действие (return, ignore, snooze, etc)
            data: данные уведомления
        """
        logger.info(f"Notification action: {notification_type} -> {action}")
        
        if action == "return":
            # Пользователь решил вернуться к работе
            logger.info("User chose to return to work")
        
        elif action == "ignore":
            # Пользователь игнорирует предупреждение
            logger.info("User ignored the notification")
        
        elif action == "snooze":
            # Пользователь отложил напоминание
            logger.info("User snoozed the notification")
