from datetime import date
from django.utils.deprecation import MiddlewareMixin
from .models import PrayerTimeFile
from .utils.prayer_times_parser import check_and_update_all_cities

class PrayerTimeAutoUpdateMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Проверяем устаревшие данные только раз в день
        last_check = request.session.get('last_data_check')
        today = date.today().isoformat()
        
        if last_check != today:
            try:
                # Проверяем и обновляем все города
                updated_count = check_and_update_all_cities()
                if updated_count > 0:
                    print(f"Автообновление: обновлено {updated_count} записей")
                request.session['last_data_check'] = today
            except Exception as e:
                print(f"Ошибка автообновления: {e}")
        
        return None