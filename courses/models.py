from django.db import models
from django.utils.text import slugify

from accounts.models import Authors
from materials.models import AudioContent, TextContent, VideoContent


class Course(models.Model):
    """Модель курса: набор уроков с автором, статусом и датами публикации"""

    STATUS_CHOICES = (
        ("draft", "Черновик"),
        ("published", "Опубликован"),
        ("archived", "В архиве"),
    )
    title = models.CharField(max_length=200, verbose_name="Название курса")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="URL-адрес")
    description = models.TextField(verbose_name="Описание курса", blank=True, null=True)
    author = models.ForeignKey(
        Authors,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Автор курса",
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="draft", verbose_name="Статус"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    published_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Дата публикации"
    )

    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"
        ordering = ("-published_at", "-created_at")

    def save(self, *args, **kwargs):
        """Автоматически генерирует уникальный slug из названия курса,
        если slug не задан, затем сохраняет запись."""
        if not self.slug and self.title:
            self.slug = slugify(self.title)
            # Если slug уже существует, добавим уникальный суффикс
            original_slug = self.slug
            counter = 1
            while Course.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        """Строковое представление курса: его название."""
        return self.title


class Lesson(models.Model):
    """Модель урока: элемент курса, привязанный к видео-, аудио- или текстовому материалу"""

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="lessons", verbose_name="Курс"
    )
    title = models.CharField(max_length=200, verbose_name="Название урока")
    description = models.TextField(blank=True, verbose_name="Описание урока")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")

    video = models.ForeignKey(
        VideoContent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Видеоматериал",
    )
    audio = models.ForeignKey(
        AudioContent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Аудиоматериал",
    )
    text = models.ForeignKey(
        TextContent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Текстовый материал",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Урок"
        verbose_name_plural = "Уроки"
        ordering = ("course", "order")

    def __str__(self):
        """Строковое представление урока: «Курс — Урок»."""
        return f"{self.course.title} — {self.title}"
