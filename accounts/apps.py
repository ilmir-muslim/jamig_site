from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Конфигурация приложения accounts"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

    def ready(self):
        """Вызывается при старте Django: активирует сигналы приложения."""
        # Активируем сигналы
        import accounts.signals  # noqa: F401
