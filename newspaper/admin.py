from django.contrib import admin

from .models import NewspaperBlock, NewspaperIssue, NewspaperSettings


class NewspaperBlockInline(admin.TabularInline):
    """Инлайн-редактор блоков (полос) выпуска газеты"""

    model = NewspaperBlock
    extra = 1
    fields = ("order", "block_type", "size", "title", "subtitle", "author_name", "photo", "photo_caption", "is_front_page",
              "advertiser_name", "advertiser_contact", "ad_price", "ad_discount", "ad_volume", "ad_paid")


@admin.register(NewspaperIssue)
class NewspaperIssueAdmin(admin.ModelAdmin):
    """Админ-панель для выпусков газеты"""

    list_display = ("number", "title", "issue_date", "status", "editor", "views_count")
    list_filter = ("status",)
    search_fields = ("title", "number", "description")
    readonly_fields = ("created_at", "updated_at", "views_count")
    prepopulated_fields = {"slug": ("title",)}  # noqa: RUF012 - стандартный паттерн Django
    inlines = [NewspaperBlockInline]  # noqa: RUF012 - стандартный паттерн Django admin
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

    list_display = ("title", "issue", "block_type", "size", "is_front_page", "order")
    list_filter = ("block_type", "size", "is_front_page", "issue")
    search_fields = ("title", "content")



@admin.register(NewspaperSettings)
class NewspaperSettingsAdmin(admin.ModelAdmin):
    """Настройки газеты: название издания, выходные данные, полосность печати."""

    list_display = ("publication_name", "print_pages", "founder", "address")

    def has_add_permission(self, request):
        # Разрешаем добавление только пока запись не создана (она одна).
        return not NewspaperSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
