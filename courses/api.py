from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.pagination import PageNumberPagination, paginate

from .models import Course
from .schemas import CourseDetailSchema, CourseSchema

router = Router(tags=["Courses"])


@router.get("/", response=list[CourseSchema])
@paginate(PageNumberPagination, page_size=12)
def list_courses(request):
    """Возвращает список опубликованных курсов с авторами (с пагинацией)."""
    return Course.objects.filter(status="published").select_related("author__user")


@router.get("/{slug}/", response=CourseDetailSchema)
def get_course(request, slug: str):
    """Возвращает детальную информацию об опубликованном курсе по slug."""
    return get_object_or_404(Course, slug=slug, status="published")
