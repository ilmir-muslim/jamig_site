import pandas as pd
from datetime import datetime, date
from main.models import PrayerTime, PrayerTimeFile

def get_available_cities_from_file(file_path):
    """Возвращает список доступных городов в файле"""
    try:
        df = pd.read_excel(file_path)
        cities = []
        
        for index, row in df.iterrows():
            if pd.isna(row.get('День')) or row.get('Город') == 'Город':
                continue
            
            city = str(row.get('Город', '')).strip()
            if city and city not in cities and city != 'Город':
                cities.append(city)
        
        return sorted(cities)
    except Exception as e:
        raise Exception(f"Ошибка получения списка городов: {e}")

def load_prayer_times_for_city(file_path, city):
    """
    Загружает времена намазов для конкретного города из файла
    Загружает только данные за текущий год
    """
    try:
        df = pd.read_excel(file_path)
        current_year = date.today().year
        prayer_times = []
        
        for index, row in df.iterrows():
            # Пропускаем заголовки и пустые строки
            if pd.isna(row.get('День')) or row.get('Город') == 'Город':
                continue
            
            # Фильтруем по городу
            row_city = str(row.get('Город', '')).strip()
            if row_city != city:
                continue
            
            # Извлекаем данные
            try:
                date_str = str(row['День']).split()[0]
                row_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                
                # Загружаем только данные за текущий год
                if row_date.year != current_year:
                    continue
                
                prayer_time_data = {
                    'city': city,
                    'date': row_date,
                    'fajr': extract_time(row['ФАДЖР']),
                    'sunrise': extract_time(row['ВОСХОД']),
                    'dhuhr': extract_time(row['Зухр']),
                    'asr': extract_time(row['АСР']),
                    'maghrib': extract_time(row['МАГРИБ']),
                    'isha': extract_time(row['ИША']),
                }
                
                # Проверяем, что все времена извлечены корректно
                if all(prayer_time_data.values()):
                    prayer_times.append(prayer_time_data)
                    
            except Exception as e:
                print(f"Ошибка в строке {index} для города {city}: {e}")
                continue
        
        return prayer_times
        
    except Exception as e:
        raise Exception(f"Ошибка парсинга Excel файла: {e}")

def update_city_prayer_times(city):
    """
    Обновляет времена намазов в базе для указанного города
    Автоматически выбирает актуальный файл
    """
    try:
        # Получаем текущий файл
        current_file = PrayerTimeFile.objects.filter(file_type='current').first()
        
        # Проверяем, не устарел ли текущий файл
        if current_file and current_file.is_data_outdated():
            # Переключаемся на предзагруженный файл
            preloaded_file = PrayerTimeFile.objects.filter(file_type='preloaded').first()
            if preloaded_file:
                # Меняем типы файлов
                current_file.file_type = 'preloaded'
                current_file.save()
                preloaded_file.file_type = 'current'
                preloaded_file.save()
                current_file = preloaded_file
                print(f"Автоматически переключились на предзагруженный файл")
            else:
                print(f"Внимание: текущий файл устарел, но предзагруженного файла нет")
        
        if not current_file:
            print(f"Нет доступного файла для города {city}")
            return 0
        
        # Получаем данные для города
        prayer_times_data = load_prayer_times_for_city(current_file.file.path, city)
        
        if not prayer_times_data:
            print(f"Нет данных для города {city} в текущем файле")
            return 0
        
        updated_count = 0
        current_year = date.today().year
        
        # Обновляем или создаем записи
        for data in prayer_times_data:
            PrayerTime.objects.update_or_create(
                city=data['city'],
                date=data['date'],
                defaults=data
            )
            updated_count += 1
        
        # Удаляем устаревшие данные (прошлые годы)
        PrayerTime.objects.filter(
            city=city,
            date__year__lt=current_year
        ).delete()
        
        print(f"Обновлено {updated_count} записей для города {city}")
        return updated_count
        
    except Exception as e:
        raise Exception(f"Ошибка обновления данных для города {city}: {e}")

def check_and_update_all_cities():
    """
    Проверяет и обновляет данные для всех городов, для которых есть данные
    """
    # Получаем все города, для которых есть данные в базе
    cities_with_data = PrayerTime.objects.values_list('city', flat=True).distinct()
    
    total_updated = 0
    for city in cities_with_data:
        try:
            count = update_city_prayer_times(city)
            total_updated += count
        except Exception as e:
            print(f"Ошибка обновления для города {city}: {e}")
    
    return total_updated

def extract_time(time_value):
    """Извлекает время из различных форматов"""
    if pd.isna(time_value):
        return None
        
    time_str = str(time_value)
    
    # Если это datetime объект
    if isinstance(time_value, datetime):
        return time_value.time()
    
    # Если строка с датой и временем
    if ' ' in time_str:
        try:
            return datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S').time()
        except:
            try:
                return datetime.strptime(time_str.split()[1], '%H:%M:%S').time()
            except:
                pass
    
    # Если только время
    try:
        return datetime.strptime(time_str, '%H:%M:%S').time()
    except:
        pass
        
    return None