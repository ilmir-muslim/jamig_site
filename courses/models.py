from django.db import models
from accounts.models import Authors
from materials.models import VideoContent, AudioContent, TextContent


class Course(models.Model):
    STATUS_CHOICES = [
        ("draft", "Черновик"),
        ("published", "Опубликован"),
        ("archived", "В архиве"),
    ]
    title = models.CharField(max_length=200, verbose_name="Название курса")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="URL-адрес")
    description = models.TextField(verbose_name="Описание курса")
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
        ordering = ["-published_at", "-created_at"]

    def __str__(self):
        return self.title


class Lesson(models.Model):
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
        ordering = ["course", "order"]

    def __str__(self):
        return f"{self.course.title} — {self.title}"
