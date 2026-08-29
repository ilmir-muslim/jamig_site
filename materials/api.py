from ninja import Router
from ninja.pagination import paginate, PageNumberPagination
from django.shortcuts import get_object_or_404
from .models import Category, VideoContent, AudioContent, TextContent
from .schemas import CategorySchema, VideoSchema, AudioSchema, TextSchema

router = Router(tags=["Materials"])


@router.get("/categories/", response=list[CategorySchema])
def list_categories(request):
    """Возвращает список активных категорий"""
    return Category.objects.filter(is_active=True)


@router.get("/videos/", response=list[VideoSchema])
@paginate(PageNumberPagination, page_size=12)
def list_videos(request, category: str = None):
    """Список опубликованных видео с опциональной фильтрацией по категории"""
    qs = VideoContent.objects.filter(status="published").select_related(
        "category", "author__user"
    )
    if category:
        qs = qs.filter(category__slug=category)
    return qs


@router.get("/videos/{slug}/", response=VideoSchema)
def get_video(request, slug: str):
    """Детальная информация о видео"""
    return get_object_or_404(VideoContent, slug=slug, status="published")


@router.get("/audios/", response=list[AudioSchema])
@paginate(PageNumberPagination, page_size=12)
def list_audios(request, category: str = None):
    """Список опубликованных аудио"""
    qs = AudioContent.objects.filter(status="published").select_related(
        "category", "author__user"
    )
    if category:
        qs = qs.filter(category__slug=category)
    return qs


@router.get("/audios/{slug}/", response=AudioSchema)
def get_audio(request, slug: str):
    """Детальная информация об аудио"""
    return get_object_or_404(AudioContent, slug=slug, status="published")


@router.get("/texts/", response=list[TextSchema])
@paginate(PageNumberPagination, page_size=12)
def list_texts(request, category: str = None):
    """Список опубликованных статей"""
    qs = TextContent.objects.filter(status="published").select_related(
        "category", "author__user"
    )
    if category:
        qs = qs.filter(category__slug=category)
    return qs


@router.get("/texts/{slug}/", response=TextSchema)
def get_text(request, slug: str):
    """Детальная информация о статье"""
    return get_object_or_404(TextContent, slug=slug, status="published")
