from django.contrib import admin
from .models import PrayerTime, Post

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

