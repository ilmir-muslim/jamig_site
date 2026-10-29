from .models import Category


def categories_processor(request):
    """Контекст-процессор: передаёт активные категории во все шаблоны
    под ключом `menu_categories` (для меню сайта)."""
    return {"menu_categories": Category.objects.filter(is_active=True)}
