# utils/notifications.py

from plyer import notification

def notify(title: str, message: str):
    """Унифицированная функция уведомлений."""
    notification.notify(title=title, message=message)
