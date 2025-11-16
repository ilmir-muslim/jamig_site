from django.contrib import admin
from django.contrib import messages
from .models import PrayerTime, Post, PrayerTimeFile
from .utils.prayer_times_parser import get_available_cities_from_file, update_city_prayer_times

@admin.register(PrayerTimeFile)
class PrayerTimeFileAdmin(admin.ModelAdmin):
    list_display = ['file_type', 'uploaded_at', 'cities_count', 'data_status']
    list_filter = ['file_type', 'uploaded_at']
    readonly_fields = ['cities_count', 'available_cities', 'data_status']
    
    def save_model(self, request, obj, form, change):
        """При сохранении файла проверяем его актуальность"""
        super().save_model(request, obj, form, change)
        
        try:
            # Если это текущий файл, загружаем данные для Муслюмово по умолчанию
            if obj.file_type == 'current':
                count = update_city_prayer_times('Муслюмово')
                messages.success(
                    request, 
                    f"Загружено {count} записей намазов для Муслюмово"
                )
            
            # Проверяем статус данных
            if obj.is_data_outdated():
                messages.warning(request, "Данные в файле устарели (нет дат текущего года)")
            else:
                messages.info(request, "Данные в файле актуальны")
                
        except Exception as e:
            messages.error(request, f"Ошибка при обработке файла: {e}")
    
    def cities_count(self, obj):
        """Количество доступных городов в файле"""
        try:
            cities = get_available_cities_from_file(obj.file.path)
            return len(cities)
        except:
            return 0
    cities_count.short_description = "Городов в файле"
    
    def available_cities(self, obj):
        """Список доступных городов"""
        try:
            cities = get_available_cities_from_file(obj.file.path)
            return ", ".join(cities)
        except:
            return "Ошибка чтения"
    available_cities.short_description = "Доступные города"
    
    def data_status(self, obj):
        """Статус данных в файле"""
        try:
            if obj.is_data_outdated():
                return "Устарели"
            else:
                return "Актуальны"
        except:
            return "Ошибка проверки"
    data_status.short_description = "Статус данных"

@admin.register(PrayerTime)
class PrayerTimeAdmin(admin.ModelAdmin):
    list_display = ['city', 'date', 'fajr', 'dhuhr', 'asr', 'maghrib', 'isha']
    list_filter = ['city', 'date']
    search_fields = ['city']
    ordering = ['-date']