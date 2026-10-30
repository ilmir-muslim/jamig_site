import pytils.translit
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class NewspaperIssue(models.Model):
    """Выпуск газеты мечети (электронная версия печатной газеты)"""

    STATUS_CHOICES = (
        ("draft", "Черновик"),
        ("published", "Опубликовано"),
        ("archived", "В архиве"),
    )

    title = models.CharField(max_length=200, verbose_name="Название выпуска")
    slug = models.SlugField(
        max_length=220, unique=True, blank=True, verbose_name="URL-адрес"
    )
    number = models.CharField(
        max_length=20, verbose_name="Номер выпуска", help_text="Например: 12 (254)"
    )
    issue_date = models.DateField(verbose_name="Дата выпуска")
    cover_image = models.ImageField(
        upload_to="newspaper/covers/%Y/%m/",
        blank=True,
        verbose_name="Обложка выпуска",
    )
    description = models.TextField(
        blank=True, verbose_name="Анонс", help_text="Краткое описание для главной страницы"
    )
    pdf_file = models.FileField(
        upload_to="newspaper/pdf/%Y/%m/",
        blank=True,
        verbose_name="PDF-версия",
        help_text="PDF печатной версии газеты (необязательно)",
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="draft", verbose_name="Статус"
    )
    editor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="edited_issues",
        verbose_name="Редактор",
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
        verbose_name = "Выпуск газеты"
        verbose_name_plural = "Выпуски газеты"
        ordering = ("-issue_date", "-created_at")

    def save(self, *args, **kwargs):
        """Генерирует slug из названия и номера выпуска, проставляет дату публикации."""
        if not self.slug:
            base = pytils.translit.slugify(f"{self.title} {self.number}")
            self.slug = slugify(base) or base
        if not self.slug:
            from django.utils.crypto import get_random_string

            self.slug = f"vypusk-{get_random_string(6)}"
        if self.status == "published" and not self.published_at:
            from django.utils import timezone

            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """Возвращает абсолютный URL страницы выпуска."""
        return reverse("newspaper_issue_detail", kwargs={"slug": self.slug})

    def __str__(self):
        """Строковое представление выпуска: номер и название."""
        return f"{self.number} — {self.title}"


BLOCK_TYPES = (
    ("article", "Статья"),
    ("interview", "Интервью"),
    ("news", "Заметка"),
    ("photo", "Фотография"),
    ("announcement", "Объявление"),
)


class NewspaperBlock(models.Model):
    """Блок (полоса) выпуска газеты: текстовая статья с фото или фотоматериал.

    Из блоков конструктора собирается классическая газетная вёрстка:
    заголовок, подзаголовок, автор, фото с подписью и текст.
    """

    title = models.CharField(max_length=250, verbose_name="Заголовок")
    subtitle = models.CharField(
        max_length=350, blank=True, verbose_name="Подзаголовок"
    )
    block_type = models.CharField(
        max_length=20, choices=BLOCK_TYPES, default="article", verbose_name="Тип блока"
    )
    content = models.TextField(
        blank=True, verbose_name="Текст", help_text="Текст материала (абзацы)"
    )
    author_name = models.CharField(
        max_length=150, blank=True, verbose_name="Автор материала"
    )
    photo = models.ImageField(
        upload_to="newspaper/blocks/%Y/%m/",
        blank=True,
        verbose_name="Фотография",
    )
    photo_caption = models.CharField(
        max_length=300, blank=True, verbose_name="Подпись к фото"
    )
    issue = models.ForeignKey(
        NewspaperIssue,
        on_delete=models.CASCADE,
        related_name="blocks",
        verbose_name="Выпуск",
    )
    order = models.PositiveIntegerField(
        default=0, verbose_name="Порядок (полоса)"
    )

    class Meta:
        verbose_name = "Блок газеты"
        verbose_name_plural = "Блоки газеты"
        ordering = ("order", "id")

    def save(self, *args, **kwargs):
        """Если порядок не задан — ставит блок в конец выпуска."""
        if not self.order:
            last = (
                NewspaperBlock.objects.filter(issue=self.issue)
                .order_by("-order")
                .values_list("order", flat=True)
                .first()
            )
            self.order = (last or 0) + 1
        super().save(*args, **kwargs)

    def get_content_html(self):
        """Возвращает текст блока в виде HTML-абзацев."""
        if not self.content:
            return ""
        paragraphs = [p.strip() for p in self.content.split("\n") if p.strip()]
        return "".join(f"<p>{p}</p>" for p in paragraphs)

    def __str__(self):
        """Строковое представление блока: его заголовок."""
        return self.title
