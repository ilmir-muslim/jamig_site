### BEGIN: main/views.py
from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse
from .models import PrayerTime, Post, PrayerTimeFile
from materials.models import VideoContent
from datetime import date
from .utils.prayer_times_parser import update_city_prayer_times
from .utils.cities_manager import get_available_cities, search_cities

def home(request):
    # Получаем последнее опубликованное видео
    try:
        current_video = (
            VideoContent.objects.filter(status="published")
            .select_related("author", "category")
            .latest("published_at")
        )
    except VideoContent.DoesNotExist:
        current_video = None

    # Получаем активный город из сессии или используем Муслюмово по умолчанию
    active_city = request.session.get('active_city', 'Муслюмово')
    current_year = date.today().year
    
    # Проверяем, есть ли актуальные данные для выбранного города
    has_current_data = PrayerTime.objects.filter(
        city=active_city,
        date__year=current_year
    ).exists()
    
    # Если данных нет или они устарели, загружаем из файла
    if not has_current_data:
        try:
            count = update_city_prayer_times(active_city)
            if count > 0:
                messages.info(request, f"Загружены данные для города {active_city}")
            else:
                # Если не удалось загрузить для выбранного города, пробуем Муслюмово
                if active_city != 'Муслюмово':
                    count_default = update_city_prayer_times('Муслюмово')
                    if count_default > 0:
                        active_city = 'Муслюмово'
                        request.session['active_city'] = active_city
                        messages.info(request, f"Данные для выбранного города недоступны. Показаны данные для Муслюмово")
        except Exception as e:
            messages.error(request, f"Ошибка загрузки данных: {e}")

    # Получаем времена намазов на текущий месяц для активного города
    today = date.today()
    prayer_times = PrayerTime.objects.filter(
        city=active_city,
        date__year=today.year, 
        date__month=today.month
    ).order_by('date')[:30]

    # Получаем список доступных городов из КЭША (JSON файла)
    available_cities = get_available_cities()

    # Получаем последние посты
    recent_posts = Post.objects.filter(is_published=True)[:5]

    context = {
        "current_video": current_video,
        "prayer_times": prayer_times,
        "recent_posts": recent_posts,
        "today": today,
        "active_city": active_city,
        "available_cities": available_cities,
        "has_prayer_data": prayer_times.exists(),
    }

    return render(request, "main/home.html", context)

def set_city(request):
    """Установка активного города"""
    if request.method == 'POST':
        city = request.POST.get('city')
        if city:
            # Проверяем, есть ли такой город в доступных
            available_cities = get_available_cities()
            if city not in available_cities:
                messages.warning(request, f"Город '{city}' не найден в расписании")
            else:
                request.session['active_city'] = city
                messages.success(request, f"Город изменен на {city}")
                
                # Пытаемся загрузить данные для нового города
                try:
                    count = update_city_prayer_times(city)
                    if count == 0:
                        messages.warning(request, f"Данные для города {city} недоступны")
                except Exception as e:
                    messages.error(request, f"Ошибка загрузки данных для города {city}")
    
    return redirect('home')

def search_cities_ajax(request):
    """AJAX endpoint для поиска городов"""
    query = request.GET.get('q', '')
    cities = search_cities(query)
    return JsonResponse({'cities': cities})
### END: main/views.py