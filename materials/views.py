from django.shortcuts import render
from django.utils import timezone
from .models import PrayerTime, Post
from materials.models import VideoContent  # Импортируем из приложения materials
from datetime import date

def home(request):
    # Получаем последнее опубликованное видео из приложения materials
    try:
        current_video = VideoContent.objects.filter(
            status='published'
        ).select_related('author', 'category').latest('published_at')
    except VideoContent.DoesNotExist:
        current_video = None
    
    # Получаем времена намазов на текущий месяц
    today = date.today()
    prayer_times = PrayerTime.objects.filter(
        date__year=today.year,
        date__month=today.month
    ).order_by('date')[:30]  # на 30 дней
    
    # Получаем последние посты
    recent_posts = Post.objects.filter(is_published=True)[:5]
    
    context = {
        'current_video': current_video,
        'prayer_times': prayer_times,
        'recent_posts': recent_posts,
        'today': today,
    }
    
    return render(request, 'main/home.html', context)