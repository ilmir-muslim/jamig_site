### BEGIN: main/admin.py
from django.contrib import admin
from django.contrib import messages
from .models import Post, PrayerTimeFile
from .utils.prayer_times_parser import check_and_update_all_cities, update_city_prayer_times
from .utils.cities_manager import update_cities_cache, get_available_cities

@admin.register(PrayerTimeFile)
class PrayerTimeFileAdmin(admin.ModelAdmin):
    list_display = ['file_type', 'uploaded_at', 'cities_count', 'data_status']
    list_filter = ['file_type', 'uploaded_at']
    readonly_fields = ['cities_count', 'data_status']
    
    def save_model(self, request, obj, form, change):
        """При сохранении файла проверяем его актуальность и обновляем кэш городов"""
        super().save_model(request, obj, form, change)
        
        try:
            # Обновляем кэш городов при загрузке любого файла
            cities = update_cities_cache()
            
            # Проверяем статус данных
            if obj.is_data_outdated():
                messages.warning(request, "Данные в файле устарели (нет дат текущего года)")
            else:
                messages.info(request, "Данные в файле актуальны")
                
            # Если это текущий файл и он актуален, загружаем данные для Муслюмово по умолчанию
            if obj.file_type == 'current' and not obj.is_data_outdated():
                count = update_city_prayer_times('Муслюмово')
                if count > 0:
                    messages.success(
                        request, 
                        f"Загружено {count} записей намазов для Муслюмово. Обновлено {len(cities)} городов в кэше."
                    )
                else:
                    messages.warning(
                        request,
                        f"Не удалось загрузить данные для Муслюмово. Обновлено {len(cities)} городов в кэше."
                    )
            else:
                messages.success(request, f"Обновлено {len(cities)} городов в кэше")
                
        except Exception as e:
            messages.error(request, f"Ошибка при обработке файла: {e}")
    
    def cities_count(self, obj):
        """Количество доступных городов в файле"""
        cities = get_available_cities()
        return len(cities)
    cities_count.short_description = "Городов в файле"
    
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

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'post_type', 'is_published', 'created_at']
    list_filter = ['post_type', 'is_published', 'created_at']
    search_fields = ['title', 'content']
    list_editable = ['is_published']
### END: main/admin.py