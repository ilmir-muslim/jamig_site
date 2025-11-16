### BEGIN: main/utils/cities_manager.py
import json
import os
from django.conf import settings
from .prayer_times_parser import get_available_cities_from_file
from main.models import PrayerTimeFile

CITIES_CACHE_FILE = os.path.join(settings.BASE_DIR, 'cities_cache.json')

def get_cities_from_cache():
    """Получает города из кэш-файла"""
    try:
        if os.path.exists(CITIES_CACHE_FILE):
            with open(CITIES_CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Ошибка чтения кэша городов: {e}")
    return []

def update_cities_cache():
    """Обновляет кэш городов из текущего файла"""
    current_file = PrayerTimeFile.objects.filter(file_type='current').first()
    if not current_file:
        print("Нет текущего файла для обновления кэша городов")
        return []
    
    try:
        cities = get_available_cities_from_file(current_file.file.path)
        with open(CITIES_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cities, f, ensure_ascii=False, indent=2)
        print(f"Кэш городов обновлен: {len(cities)} городов")
        return cities
    except Exception as e:
        print(f"Ошибка обновления кэша городов: {e}")
        return []

def get_available_cities():
    """Основная функция для получения списка городов"""
    cities = get_cities_from_cache()
    if not cities:
        cities = update_cities_cache()
    return cities

def search_cities(query):
    """Поиск городов по запросу"""
    cities = get_available_cities()
    if not query:
        return cities
    
    query_lower = query.lower()
    return [city for city in cities if query_lower in city.lower()]
### END: main/utils/cities_manager.py