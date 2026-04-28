from django.db import models


class Post(models.Model):
    POST_TYPES = [
        ("news", "Новость"),
        ("article", "Статья"),
        ("lesson", "Урок"),
    ]

    title = models.CharField(max_length=200, verbose_name="Заголовок")
    content = models.TextField(verbose_name="Содержание")
    post_type = models.CharField(
        max_length=10, choices=POST_TYPES, verbose_name="Тип поста"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    is_published = models.BooleanField(default=True, verbose_name="Опубликовано")

    class Meta:
        verbose_name = "Пост"
        verbose_name_plural = "Посты"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
