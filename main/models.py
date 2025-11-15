from django.db import models

class PrayerTime(models.Model):
    date = models.DateField(unique=True, verbose_name="Дата")
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

