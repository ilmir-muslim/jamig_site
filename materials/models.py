import re

import pytils.translit
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from accounts.models import Authors
from jamig_site import settings


class Category(models.Model):
    """Модель категории для группировки материалов сайта"""

    title = models.CharField(max_length=200, verbose_name="Название")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="URL-адрес")
    description = models.TextField(blank=True, verbose_name="Описание")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок сортировки")
    is_active = models.BooleanField(default=True, verbose_name="Активная")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ("order", "title")

    def __str__(self):
        """Строковое представление категории: её название."""
        return self.title


class BaseContent(models.Model):
    """Абстрактная базовая модель контента: общие поля, генерация slug и дат"""

    STATUS_CHOICES = (
        ("draft", "Черновик"),
        ("published", "Опубликовано"),
        ("archived", "В архиве"),
    )

    title = models.CharField(max_length=200, verbose_name="Название")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="URL-адрес")
    description = models.TextField(blank=True, verbose_name="Описание")
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Категория",
    )
    author = models.ForeignKey(
        Authors, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Автор"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="draft", verbose_name="Статус"
    )
    views_count = models.PositiveIntegerField(
        default=0, verbose_name="Количество просмотров"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    published_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Дата публикации"
    )

    class Meta:
        abstract = True
        ordering = ("-published_at", "-created_at")

    def save(self, *args, **kwargs):
        """Автоматически генерирует slug из названия (транслитерация),
        а при публикации проставляет дату published_at."""
        if not self.slug:
            if self.title:
                base = pytils.translit.slugify(self.title)
                self.slug = slugify(base) or base
            if not self.slug:
                from django.utils.crypto import get_random_string

                self.slug = f"bez-nazvaniya-{get_random_string(6)}"
        if self.status == "published" and not self.published_at:
            from django.utils import timezone

            self.published_at = timezone.now()
        super().save(*args, **kwargs)


class VideoContent(BaseContent):
    """Модель видеоматериала: код встраивания, длительность, обложка, прямой эфир"""

    embed_code = models.TextField(
        verbose_name="Код вставки или ссылка на видео",
        help_text="Вставьте iframe-код или прямую ссылку на видео (Rutube, YouTube и др.)",
        blank=True,
        default="",
    )
    duration = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Длительность (секунды)"
    )
    thumbnail = models.ImageField(
        upload_to="video_thumbnails/", blank=True, verbose_name="Обложка видео"
    )
    is_live = models.BooleanField(default=False, verbose_name="Прямой эфир")

    def get_absolute_url(self):
        """Возвращает абсолютный URL страницы видео."""
        return reverse("video_detail", kwargs={"slug": self.slug})

    def get_embed_html(self):
        """Возвращает HTML для встраивания видео."""
        if not self.embed_code:
            return '<div class="alert alert-info">Видео недоступно</div>'

        # Если это уже iframe – возвращаем как есть
        if "<iframe" in self.embed_code:
            return self.embed_code

        # Иначе пытаемся интерпретировать как ссылку
        embed = self._url_to_iframe(self.embed_code.strip())
        if embed:
            return embed

        # Ничего не подошло
        return '<div class="alert alert-warning">Неверный формат видео</div>'

    @staticmethod
    def _url_to_iframe(url: str) -> str | None:
        """Пытается преобразовать ссылку на видео в iframe-код."""
        # Rutube: https://rutube.ru/video/<id>/...
        match = re.search(r"rutube\.ru/video/(?P<id>[a-f0-9]+)", url)
        if match:
            video_id = match.group("id")
            return (
                f'<iframe width="720" height="405" '
                f'src="https://rutube.ru/play/embed/{video_id}" '
                f'frameborder="0" allowfullscreen></iframe>'
            )
        # Здесь можно добавить YouTube, VK и т.д.
        return None

    def extract_video_id(self):
        """Извлекает ID видео Rutube из кода вставки, либо None."""
        import re

        if self.embed_code:
            # Ищем video_id в коде iframe
            pattern = r"rutube\.ru/play/embed/([a-zA-Z0-9]+)"
            match = re.search(pattern, self.embed_code)
            if match:
                return match.group(1)
        return None

    class Meta:
        verbose_name = "Видео"
        verbose_name_plural = "Видео"


class AudioContent(BaseContent):
    """Модель аудиоматериала: аудиофайл, длительность, обложка и прослушивания"""

    audio_file = models.FileField(
        upload_to="audio/%Y/%m/%d/",
        verbose_name="Аудиофайл",
        help_text="Загрузите аудиофайл в формате MP3, WAV, OGG",
    )
    duration = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Длительность (секунды)"
    )
    cover_image = models.ImageField(
        upload_to="audio_covers/%Y/%m/%d/", blank=True, verbose_name="Обложка аудио"
    )
    listens_count = models.PositiveIntegerField(
        default=0, verbose_name="Количество прослушиваний"
    )

    def get_absolute_url(self):
        """Возвращает абсолютный URL страницы аудио."""
        return reverse("audio_detail", kwargs={"slug": self.slug})

    def get_duration_display(self):
        """Возвращает длительность в формате «ММ:СС», либо «00:00»."""
        if self.duration:
            minutes = self.duration // 60
            seconds = self.duration % 60
            return f"{minutes:02d}:{seconds:02d}"
        return "00:00"

    def get_file_size(self):
        """Возвращает размер аудиофайла в человекочитаемом виде (КБ/МБ)."""
        if self.audio_file:
            size = self.audio_file.size
            if size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size / (1024 * 1024):.1f} MB"
        return "0 KB"

    class Meta:
        verbose_name = "Аудио"
        verbose_name_plural = "Аудио"


class TextContent(BaseContent):
    """Модель текстовой статьи: подзаголовок, содержание и время чтения"""

    subtitle = models.CharField(max_length=300, blank=True, verbose_name="Подзаголовок")
    content = models.TextField(verbose_name="Содержание", blank=True, null=True)
    cover_image = models.ImageField(
        upload_to="text_covers/%Y/%m/%d/", blank=True, verbose_name="Обложка статьи"
    )
    reading_time = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Время чтения (минуты)"
    )

    def save(self, *args, **kwargs):
        """Подсчитывает время чтения (примерно 200 слов в минуту),
        если оно ещё не указано."""
        if not self.reading_time and self.content:
            word_count = len(self.content.split())
            self.reading_time = max(1, word_count // 200)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """Возвращает абсолютный URL читалки статьи."""
        return reverse("text_reader", kwargs={"slug": self.slug})

    class Meta:
        verbose_name = "Текстовая статья"
        verbose_name_plural = "Текстовые статьи"


class ReadingProgress(models.Model):
    """Модель прогресса чтения статьи пользователем (номер страницы)"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Пользователь"
    )
    text = models.ForeignKey(
        TextContent, on_delete=models.CASCADE, verbose_name="Статья"
    )
    page_number = models.PositiveIntegerField(default=1, verbose_name="Номер страницы")
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Последнее обновление"
    )

    class Meta:
        verbose_name = "Прогресс чтения"
        verbose_name_plural = "Прогресс чтения"
        unique_together = ("user", "text")

    def __str__(self):
        """Строковое представление: пользователь, статья и номер страницы."""
        return f"{self.user} — {self.text.title} (стр. {self.page_number})"
