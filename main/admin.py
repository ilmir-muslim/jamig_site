from django.contrib import admin
from .models import PrayerTime, Post, VideoContent

@admin.register(PrayerTime)
class PrayerTimeAdmin(admin.ModelAdmin):
    list_display = ['date', 'fajr', 'dhuhr', 'asr', 'maghrib', 'isha']
    list_filter = ['date']
    ordering = ['-date']

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'post_type', 'created_at', 'is_published']
    list_filter = ['post_type', 'is_published', 'created_at']
    search_fields = ['title', 'content']

@admin.register(VideoContent)
class VideoContentAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_live', 'is_active', 'created_at']
    list_filter = ['is_live', 'is_active']
    search_fields = ['title']