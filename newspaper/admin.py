from django.contrib import admin

from .models import NewspaperBlock, NewspaperIssue


class NewspaperBlockInline(admin.TabularInline):
    """Инлайн-редактор блоков (полос) выпуска газеты"""

    model = NewspaperBlock
    extra = 1
    fields = ("order", "block_type", "title", "subtitle", "author_name", "photo", "photo_caption")


@admin.register(NewspaperIssue)
class NewspaperIssueAdmin(admin.ModelAdmin):
    """Админ-панель для выпусков газеты"""

    list_display = ("number", "title", "issue_date", "status", "editor", "views_count")
    list_filter = ("status",)
    search_fields = ("title", "number", "description")
    readonly_fields = ("created_at", "updated_at", "views_count")
    prepopulated_fields = {"slug": ("title",)}  # noqa: RUF012 - стандартный паттерн Django
    inlines = [NewspaperBlockInline]
    fieldsets = (
        (
            "Основная информация",
            {"fields": ("title", "slug", "number", "issue_date", "description", "editor")},
        ),
        ("Медиа", {"fields": ("cover_image", "pdf_file")}),
        ("Настройки", {"fields": ("status", "published_at")}),
        ("Статистика", {"fields": ("views_count", "created_at", "updated_at")}),
    )


@admin.register(NewspaperBlock)
class NewspaperBlockAdmin(admin.ModelAdmin):
    """Админ-панель для блоков газеты"""

    list_display = ("title", "issue", "block_type", "order")
    list_filter = ("block_type", "issue")
    search_fields = ("title", "content")
