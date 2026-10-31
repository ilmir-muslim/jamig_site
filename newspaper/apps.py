from django.apps import AppConfig


class NewspaperConfig(AppConfig):
    """Конфигурация приложения «Газета» (электронная версия газеты мечети)"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "newspaper"
    verbose_name = "Газета"
