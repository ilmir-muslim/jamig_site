from django.db import OperationalError, ProgrammingError

from .models import NewspaperIssue


def latest_newspaper_issue(request):
    """Добавляет в контекст шаблонов последний опубликованный выпуск газеты
    (для анонса на главной странице и кнопки в меню)."""
    try:
        latest_issue = NewspaperIssue.objects.filter(status="published").first()
    except (OperationalError, ProgrammingError):
        # Таблица газеты ещё не создана (миграции не выполнены) — скрываем блок.
        latest_issue = None
    return {"latest_newspaper_issue": latest_issue}
