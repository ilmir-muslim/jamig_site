from ninja import Router
from ninja.pagination import PageNumberPagination, paginate

from accounts.models import Authors
from courses.models import Course
from materials.models import VideoContent
from materials.schemas import AuthorSchema

from .models import Post
from .schemas import HomeSchema, PostSchema

router = Router(tags=["Main"])


@router.get("/home/", response=HomeSchema)
def get_home(request):
    """Агрегирует данные для главной страницы (BFF): актуальное видео,
    последние посты, авторов и активные курсы."""
    try:
        current_video = (
            VideoContent.objects.filter(status="published")
            .select_related("author__user", "category")
            .latest("published_at")
        )
    except VideoContent.DoesNotExist:
        current_video = None

    recent_posts = list(Post.objects.filter(is_published=True)[:5])
    authors = list(
        Authors.objects.filter(show_in_authors_list=True).select_related("user")[:4]
    )
    active_courses = list(
        Course.objects.filter(status="published").select_related("author__user")[:3]
    )

    return {
        "current_video": current_video,
        "recent_posts": recent_posts,
        "authors": authors,
        "active_courses": active_courses,
    }


@router.get("/posts/", response=list[PostSchema])
@paginate(PageNumberPagination, page_size=10)
def list_posts(request, post_type: str | None = None):
    """Возвращает опубликованные посты с опциональной фильтрацией по типу
    (news / article / lesson), с пагинацией."""
    qs = Post.objects.filter(is_published=True)
    if post_type:
        qs = qs.filter(post_type=post_type)
    return qs


@router.get("/authors/", response=list[AuthorSchema])
def list_authors(request):
    """Возвращает список авторов, отображаемых в публичном списке."""
    return Authors.objects.filter(show_in_authors_list=True).select_related("user")
