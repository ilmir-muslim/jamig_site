from ninja import Router
from ninja.pagination import paginate, PageNumberPagination
from .models import Post
from accounts.models import Authors
from materials.models import VideoContent
from courses.models import Course
from .schemas import PostSchema, HomeSchema
from materials.schemas import AuthorSchema

router = Router(tags=["Main"])


@router.get("/home/", response=HomeSchema)
def get_home(request):
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
def list_posts(request, post_type: str = None):
    qs = Post.objects.filter(is_published=True)
    if post_type:
        qs = qs.filter(post_type=post_type)
    return qs


@router.get("/authors/", response=list[AuthorSchema])
def list_authors(request):
    return Authors.objects.filter(show_in_authors_list=True).select_related("user")
