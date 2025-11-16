### BEGIN: main/utils/prayer_times_parser.py
import pandas as pd
from datetime import datetime, date
from main.models import PrayerTime, PrayerTimeFile

def get_available_cities_from_file(file_path):
    """Возвращает список доступных городов в файле"""
    try:
        print(f"Чтение файла для получения городов: {file_path}")
        
        # Читаем файл, пропуская первые 2 строки (заголовки)
        # Используем header=None, потому что у нас нет заголовков после пропуска
        df = pd.read_excel(file_path, skiprows=2, header=None)
        
        cities = []
        current_city = None
        
        for index, row in df.iterrows():
            # Проверяем, что строка не пустая
            if pd.isna(row[0]) and pd.isna(row[1]):
                continue
            
            # Колонка A (индекс 0) - город
            city_value = row[0]
            
            # Если в колонке города есть значение - это новый город
            if not pd.isna(city_value):
                current_city = str(city_value).strip()
                if (current_city and 
                    current_city not in cities and 
                    current_city not in ['Город', 'Торак пункт']):
                    cities.append(current_city)
                    print(f"Найден город: {current_city}")
        
        cities_list = sorted(cities)
        print(f"Всего найдено городов: {len(cities_list)}")
        return cities_list
        
    except Exception as e:
        print(f"Ошибка получения списка городов: {e}")
        return []

def parse_date_from_excel(date_value):
    """Парсит дату из Excel формата"""
    if pd.isna(date_value):
        return None
    
    try:
        # Если это уже datetime объект
        if isinstance(date_value, (datetime, pd.Timestamp)):
            return date_value.date()
        
        date_str = str(date_value)
        # Берем только часть до пробела (дату без времени)
        date_part = date_str.split()[0]
        
        # Парсим дату в формате YYYY-MM-DD
        return datetime.strptime(date_part, '%Y-%m-%d').date()
        
    except Exception as e:
        print(f"Ошибка парсинга даты '{date_value}': {e}")
        return None

def parse_time_from_excel(time_value):
    """Парсит время из Excel формата"""
    if pd.isna(time_value):
        return None
    
    try:
        # Если это уже datetime объект
        if isinstance(time_value, (datetime, pd.Timestamp)):
            return time_value.time()
        
        time_str = str(time_value)
        
        # Если строка содержит дату и время, извлекаем время
        if ' ' in time_str:
            time_part = time_str.split()[1]
            return datetime.strptime(time_part, '%H:%M:%S').time()
        else:
            # Если только время
            return datetime.strptime(time_str, '%H:%M:%S').time()
            
    except Exception as e:
        print(f"Ошибка парсинга времени '{time_value}': {e}")
        return None

def load_prayer_times_for_city(file_path, city):
    """
    Загружает времена намазов для конкретного города из файла
    Загружает только данные за текущий год
    """
    try:
        print(f"Загрузка данных для города '{city}' из файла {file_path}")
        
        # Читаем файл, пропуская первые 2 строки
        df = pd.read_excel(file_path, skiprows=2, header=None)
        
        current_year = date.today().year
        prayer_times = []
        current_city = None
        city_data_found = False
        
        for index, row in df.iterrows():
            # Проверяем, что строка не пустая
            if pd.isna(row[0]) and pd.isna(row[1]):
                continue
            
            # Колонка A (индекс 0) - город
            city_value = row[0]
            
            # Если в колонке города есть значение - это новый город
            if not pd.isna(city_value):
                current_city = str(city_value).strip()
                print(f"Обрабатываем город: {current_city}")
            
            # Если это не наш город, пропускаем
            if current_city != city:
                continue
            
            city_data_found = True
            
            # Извлекаем данные для нашего города
            try:
                # Колонка B (индекс 1) - дата
                row_date = parse_date_from_excel(row[1])
                if not row_date:
                    print(f"Не удалось распарсить дату в строке {index}: {row[1]}")
                    continue
                
                # Загружаем только данные за текущий год
                if row_date.year != current_year:
                    print(f"Пропускаем данные за {row_date.year} год")
                    continue
                
                prayer_time_data = {
                    'city': city,
                    'date': row_date,
                    # Колонка D (индекс 3) - Фаджр
                    'fajr': parse_time_from_excel(row[3]),
                    # Колонка E (индекс 4) - Восход
                    'sunrise': parse_time_from_excel(row[4]),
                    # Колонка G (индекс 6) - Зухр
                    'dhuhr': parse_time_from_excel(row[6]),
                    # Колонка H (индекс 7) - Аср
                    'asr': parse_time_from_excel(row[7]),
                    # Колонка I (индекс 8) - Магриб
                    'maghrib': parse_time_from_excel(row[8]),
                    # Колонка J (индекс 9) - Иша
                    'isha': parse_time_from_excel(row[9]),
                }
                
                # Проверяем, что все времена извлечены корректно
                if all(value is not None for value in prayer_time_data.values()):
                    prayer_times.append(prayer_time_data)
                    print(f"Успешно загружены данные для {row_date}")
                else:
                    missing_fields = [k for k, v in prayer_time_data.items() if v is None]
                    print(f"Пропущена строка {index} из-за отсутствующих данных: {missing_fields}")
                    
            except Exception as e:
                print(f"Ошибка в строке {index} для города {city}: {e}")
                continue
        
        if not city_data_found:
            print(f"Данные для города '{city}' не найдены в файле")
        else:
            print(f"Загружено {len(prayer_times)} записей для города {city}")
        
        return prayer_times
        
    except Exception as e:
        raise Exception(f"Ошибка парсинга Excel файла: {e}")

def update_city_prayer_times(city):
    """
    Обновляет времена намазов в базе для указанного города
    """
    try:
        # Получаем текущий файл
        current_file = PrayerTimeFile.objects.filter(file_type='current').first()
        
        if not current_file:
            print(f"Нет доступного файла для города {city}")
            return 0
        
        # Проверяем актуальность файла
        if current_file.is_data_outdated():
            print(f"Файл устарел для города {city}")
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
            obj, created = PrayerTime.objects.update_or_create(
                city=data['city'],
                date=data['date'],
                defaults=data
            )
            updated_count += 1
            if created:
                print(f"Создана новая запись для {data['date']}")
            else:
                print(f"Обновлена существующая запись для {data['date']}")
        
        # Удаляем устаревшие данные (прошлые годы)
        deleted_count, _ = PrayerTime.objects.filter(
            city=city,
            date__year__lt=current_year
        ).delete()
        
        print(f"Обновлено {updated_count} записей для города {city}, удалено {deleted_count} устаревших")
        return updated_count
        
    except Exception as e:
        raise Exception(f"Ошибка обновления данных для города {city}: {e}")

def check_and_update_all_cities():
    """
    Проверяет и обновляет данные для всех городов, для которых есть данные в БАЗЕ
    (только те города, которые уже были запрошены пользователями)
    """
    # Получаем только те города, которые уже есть в базе (были запрошены)
    cities_in_db = PrayerTime.objects.values_list('city', flat=True).distinct()
    
    total_updated = 0
    for city in cities_in_db:
        try:
            count = update_city_prayer_times(city)
            total_updated += count
        except Exception as e:
            print(f"Ошибка обновления для города {city}: {e}")
    
    return total_updated
### END: main/utils/prayer_times_parser.py