from .models import NewspaperIssue


def latest_newspaper_issue(request):
    """Добавляет в контекст шаблонов последний опубликованный выпуск газеты
    (для анонса на главной странице и кнопки в меню)."""
    try:
        latest_issue = NewspaperIssue.objects.filter(status="published").first()
    except Exception:
        latest_issue = None
    return {"latest_newspaper_issue": latest_issue}
