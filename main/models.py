### BEGIN: main/models.py
from datetime import date
import os
from django.db import models

class PrayerTime(models.Model):
    city = models.CharField(max_length=100, verbose_name="Город", default='Муслюмово')
    date = models.DateField(verbose_name="Дата")
    fajr = models.TimeField(verbose_name="Фаджр")
    sunrise = models.TimeField(verbose_name="Восход")
    dhuhr = models.TimeField(verbose_name="Зухр")
    asr = models.TimeField(verbose_name="Аср")
    maghrib = models.TimeField(verbose_name="Магриб")
    isha = models.TimeField(verbose_name="Иша")
    
    class Meta:
        verbose_name = "Время намаза"
        verbose_name_plural = "Времена намазов"
        ordering = ['-date']
        unique_together = ['city', 'date']
    
    def is_outdated(self):
        """Проверяет, устарели ли данные (прошлый год)"""
        return self.date.year < date.today().year

class Post(models.Model):
    POST_TYPES = [
        ('news', 'Новость'),
        ('article', 'Статья'),
        ('lesson', 'Урок'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    content = models.TextField(verbose_name="Содержание")
    post_type = models.CharField(max_length=10, choices=POST_TYPES, verbose_name="Тип поста")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    is_published = models.BooleanField(default=True, verbose_name="Опубликовано")
    
    class Meta:
        verbose_name = "Пост"
        verbose_name_plural = "Посты"
        ordering = ['-created_at']

class PrayerTimeFile(models.Model):
    FILE_TYPES = [
        ('current', 'Текущий файл'),
        ('preloaded', 'Предзагруженный файл'),
    ]
    
    file = models.FileField(upload_to='prayer_times/', verbose_name="Excel файл с расписанием")
    file_type = models.CharField(max_length=10, choices=FILE_TYPES, default='current', verbose_name="Тип файла")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Файл расписания намазов"
        verbose_name_plural = "Файлы расписания намазов"
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.get_file_type_display()} ({self.uploaded_at.date()})"
    
    def save(self, *args, **kwargs):
        # При сохранении нового файла определенного типа удаляем старые файлы этого типа
        if not self.pk:
            PrayerTimeFile.objects.filter(file_type=self.file_type).delete()
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Удаляем файл с диске при удалении записи"""
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super().delete(*args, **kwargs)
    
    def is_data_outdated(self):
        """Проверяет, устарели ли данные в файле - TRUE если нет данных за текущий год"""
        try:
            import pandas as pd
            from datetime import datetime
            
            # Читаем файл, пропуская первые 2 строки (заголовки)
            df = pd.read_excel(self.file.path, skiprows=2, header=None)
            
            current_year = date.today().year
            has_current_year_data = False
            
            print(f"Проверка актуальности файла, текущий год: {current_year}")
            
            for index, row in df.iterrows():
                # Проверяем, что строка не пустая
                if pd.isna(row[0]) or pd.isna(row[1]):
                    continue
                
                try:
                    # Колонка B (индекс 1) - дата
                    date_value = row[1]
                    date_str = str(date_value).split()[0]  # Берем только дату без времени
                    row_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    
                    print(f"Строка {index}: дата {row_date}, год: {row_date.year}")
                    
                    # Если находим дату текущего года - файл актуален
                    if row_date.year == current_year:
                        has_current_year_data = True
                        print(f"Найдены актуальные данные за {current_year} год!")
                        break
                        
                except Exception as e:
                    print(f"Ошибка обработки строки {index}: {e}")
                    continue
            
            print(f"Результат проверки актуальности: {'АКТУАЛЕН' if has_current_year_data else 'УСТАРЕЛ'}")
            # Файл устарел только если нет данных за текущий год
            return not has_current_year_data
            
        except Exception as e:
            print(f"Ошибка проверки актуальности файла: {e}")
            return True
### END: main/models.py