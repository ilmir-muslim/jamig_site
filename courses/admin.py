from django.contrib import admin
from .models import Course, Lesson


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0
    fields = ["title", "order", "video", "audio", "text"]


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "status", "published_at"]
    list_filter = ["status", "author"]
    search_fields = ["title"]
    prepopulated_fields = {"slug": ("title",)}
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ["title", "course", "order"]
    list_filter = ["course"]
    search_fields = ["title"]
