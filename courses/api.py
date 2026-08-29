from ninja import Router
from ninja.pagination import paginate, PageNumberPagination
from django.shortcuts import get_object_or_404
from .models import Course
from .schemas import CourseSchema, CourseDetailSchema

router = Router(tags=["Courses"])


@router.get("/", response=list[CourseSchema])
@paginate(PageNumberPagination, page_size=12)
def list_courses(request):
    return Course.objects.filter(status="published").select_related("author__user")


@router.get("/{slug}/", response=CourseDetailSchema)
def get_course(request, slug: str):
    return get_object_or_404(Course, slug=slug, status="published")
