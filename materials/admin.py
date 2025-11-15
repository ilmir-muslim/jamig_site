### BEGIN: materials/admin.py
from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Category, VideoContent, AudioContent, TextContent


class BaseContentAdmin(admin.ModelAdmin):
    """Базовый класс админки для контента"""
    
    list_display = ['title', 'author', 'status', 'published_at', 'views_count']
    list_filter = ['status', 'category', 'author']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at', 'views_count']
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'slug', 'description', 'category', 'author')
        }),
        ('Настройки', {
            'fields': ('status', 'published_at')
        }),
        ('Статистика', {
            'fields': ('views_count', 'created_at', 'updated_at')
        }),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['title']
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ['order', 'is_active']


@admin.register(VideoContent)
class VideoContentAdmin(BaseContentAdmin):
    list_display = BaseContentAdmin.list_display + ['is_live', 'video_preview']
    list_filter = BaseContentAdmin.list_filter + ['is_live']
    readonly_fields = BaseContentAdmin.readonly_fields + ['video_preview']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'slug', 'description', 'category', 'author')
        }),
        ('Видео контент', {
            'fields': ('embed_code', 'duration', 'thumbnail', 'is_live')
        }),
        ('Настройки', {
            'fields': ('status', 'published_at')
        }),
        ('Статистика', {
            'fields': ('views_count', 'created_at', 'updated_at', 'video_preview')
        }),
    )
    
    def video_preview(self, obj):
        if obj.pk and obj.embed_code:
            return mark_safe(
                f'<div style="margin-top: 10px;">'
                f'<h4>Предпросмотр:</h4>'
                f'<div style="max-width: 400px;">{obj.embed_code}</div>'
                f'</div>'
            )
        return "Добавьте код вставки для предпросмотра"
    video_preview.short_description = "Предпросмотр видео"


@admin.register(AudioContent)
class AudioContentAdmin(BaseContentAdmin):
    list_display = BaseContentAdmin.list_display + ['listens_count', 'duration_display', 'file_size_display']
    readonly_fields = BaseContentAdmin.readonly_fields + ['duration_display', 'file_size_display']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'slug', 'description', 'category', 'author')
        }),
        ('Аудио контент', {
            'fields': ('audio_file', 'duration', 'cover_image')
        }),
        ('Настройки', {
            'fields': ('status', 'published_at')
        }),
        ('Статистика', {
            'fields': ('views_count', 'listens_count', 'created_at', 'updated_at', 'duration_display', 'file_size_display')
        }),
    )
    
    def duration_display(self, obj):
        return obj.get_duration_display()
    duration_display.short_description = "Длительность"
    
    def file_size_display(self, obj):
        return obj.get_file_size()
    file_size_display.short_description = "Размер файла"


@admin.register(TextContent)
class TextContentAdmin(BaseContentAdmin):
    list_display = BaseContentAdmin.list_display + ['reading_time']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'slug', 'subtitle', 'content', 'category', 'author')
        }),
        ('Медиа', {
            'fields': ('cover_image',)
        }),
        ('Настройки', {
            'fields': ('status', 'reading_time', 'published_at')
        }),
        ('Статистика', {
            'fields': ('views_count', 'created_at', 'updated_at')
        }),
    )
### END: materials/admin.py