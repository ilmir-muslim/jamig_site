from django.contrib import admin

from .models import Course, Lesson


class LessonInline(admin.TabularInline):
    """Inline-форма уроков в админке курса"""

    model = Lesson
    extra = 0
    fields = ("title", "order", "video", "audio", "text")


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Админ-панель для курсов"""

    list_display = ("title", "author", "status", "published_at")
    list_filter = ("status", "author")
    search_fields = ("title",)
    prepopulated_fields = {"slug": ("title",)}  # noqa: RUF012 - словарь, стандартный паттерн Django
    inlines = (LessonInline,)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    """Админ-панель для уроков"""

    list_display = ("title", "course", "order")
    list_filter = ("course",)
    search_fields = ("title",)
