### BEGIN: materials/models.py
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from accounts.models import Authors


class Category(models.Model):
    title = models.CharField(max_length=200, verbose_name="Название")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="URL-адрес")
    description = models.TextField(blank=True, verbose_name="Описание")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок сортировки")
    is_active = models.BooleanField(default=True, verbose_name="Активная")
    
    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['order', 'title']
    
    def __str__(self):
        return self.title


class BaseContent(models.Model):
    """Абстрактная базовая модель для всего контента"""
    
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('published', 'Опубликовано'),
        ('archived', 'В архиве'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Название")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="URL-адрес")
    description = models.TextField(blank=True, verbose_name="Описание")
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Категория"
    )
    author = models.ForeignKey(
        Authors,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Автор"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name="Статус"
    )
    views_count = models.PositiveIntegerField(default=0, verbose_name="Количество просмотров")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    published_at = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name="Дата публикации"
    )
    
    class Meta:
        abstract = True
        ordering = ['-published_at', '-created_at']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if self.status == 'published' and not self.published_at:
            from django.utils import timezone
            self.published_at = timezone.now()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title


class VideoContent(BaseContent):
    """Модель для видео контента"""
    
    embed_code = models.TextField(
        verbose_name="Код вставки видео",
        help_text="Вставьте код iframe для встраивания видео с Rutube"
    )
    duration = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        verbose_name="Длительность (секунды)"
    )
    thumbnail = models.ImageField(
        upload_to='video_thumbnails/',
        blank=True,
        verbose_name="Обложка видео"
    )
    is_live = models.BooleanField(default=False, verbose_name="Прямой эфир")
    
    def get_absolute_url(self):
        return reverse('video_detail', kwargs={'slug': self.slug})
    
    def get_embed_html(self):
        """Возвращает код для вставки видео"""
        if self.embed_code:
            return self.embed_code
        return '<div class="alert alert-info">Видео недоступно</div>'
    
    def extract_video_id(self):
        """
        Извлекает ID видео из кода вставки для использования в превью
        """
        import re
        if self.embed_code:
            # Ищем video_id в коде iframe
            pattern = r'rutube\.ru/play/embed/([a-zA-Z0-9]+)'
            match = re.search(pattern, self.embed_code)
            if match:
                return match.group(1)
        return None
    
    class Meta:
        verbose_name = "Видео"
        verbose_name_plural = "Видео"


class AudioContent(BaseContent):
    """Модель для аудио контента"""
    
    audio_file = models.FileField(
        upload_to='audio/%Y/%m/%d/',
        verbose_name="Аудиофайл",
        help_text="Загрузите аудиофайл в формате MP3, WAV, OGG"
    )
    duration = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        verbose_name="Длительность (секунды)",
        help_text="Длительность аудио в секундах"
    )
    cover_image = models.ImageField(
        upload_to='audio_covers/%Y/%m/%d/',
        blank=True,
        verbose_name="Обложка аудио"
    )
    listens_count = models.PositiveIntegerField(default=0, verbose_name="Количество прослушиваний")
    
    def get_absolute_url(self):
        return reverse('audio_detail', kwargs={'slug': self.slug})
    
    def get_duration_display(self):
        """Возвращает длительность в формате MM:SS"""
        if self.duration:
            minutes = self.duration // 60
            seconds = self.duration % 60
            return f"{minutes:02d}:{seconds:02d}"
        return "00:00"
    
    def get_file_size(self):
        """Возвращает размер файла в читаемом формате"""
        if self.audio_file:
            size = self.audio_file.size
            if size < 1024 * 1024:  # Меньше 1 MB
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size / (1024 * 1024):.1f} MB"
        return "0 KB"
    
    class Meta:
        verbose_name = "Аудио"
        verbose_name_plural = "Аудио"


class TextContent(BaseContent):
    """Модель для текстового контента"""
    
    subtitle = models.CharField(max_length=300, blank=True, verbose_name="Подзаголовок")
    content = models.TextField(verbose_name="Содержание")
    cover_image = models.ImageField(
        upload_to='text_covers/%Y/%m/%d/',
        blank=True,
        verbose_name="Обложка статьи"
    )
    reading_time = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        verbose_name="Время чтения (минуты)",
        help_text="Примерное время чтения статьи в минутах"
    )
    
    def save(self, *args, **kwargs):
        # Автоматически рассчитываем время чтения если не указано
        if not self.reading_time and self.content:
            # Примерная формула: 200 слов в минуту
            word_count = len(self.content.split())
            self.reading_time = max(1, word_count // 200)
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('text_detail', kwargs={'slug': self.slug})
    
    class Meta:
        verbose_name = "Текстовая статья"
        verbose_name_plural = "Текстовые статьи"
### END: materials/models.py