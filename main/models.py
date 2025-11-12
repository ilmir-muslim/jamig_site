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

class VideoContent(models.Model):
    title = models.CharField(max_length=200, verbose_name="Название")
    rutube_url = models.URLField(verbose_name="Ссылка на Rutube", blank=True)
    rutube_embed_code = models.TextField(
        verbose_name="Код для вставки Rutube", 
        blank=True,
        help_text="Скопируйте код embed с сайта Rutube"
    )
    is_live = models.BooleanField(default=False, verbose_name="Прямой эфир")
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    
    def get_embed_html(self):
        if self.rutube_embed_code:
            return self.rutube_embed_code
        elif self.rutube_url:
            # Преобразуем обычную ссылку в embed
            video_id = self.extract_video_id(self.rutube_url)
            if video_id:
                return f'<iframe src="https://rutube.ru/play/embed/{video_id}" allow="clipboard-write; autoplay" webkitAllowFullScreen mozallowfullscreen allowFullScreen></iframe>'
        return '<div class="alert alert-info">Видео недоступно</div>'
    
    def extract_video_id(self, url):
        # Пытаемся извлечь ID видео из URL
        import re
        patterns = [
            r'rutube\.ru/play/embed/([a-zA-Z0-9]+)',
            r'rutube\.ru/video/([a-zA-Z0-9]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    class Meta:
        verbose_name = "Видео"
        verbose_name_plural = "Видео"
        ordering = ['-created_at']
