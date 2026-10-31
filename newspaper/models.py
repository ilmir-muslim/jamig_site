import json
import os
import re

import pytils.translit
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class NewspaperSettings(models.Model):
    """Глобальные настройки газеты (одна запись). Название издания редакторы
    могут менять прямо в конструкторе — оно подставляется в мачту печатной
    версии и на страницы сайта."""

    publication_name = models.CharField(
        max_length=200,
        default="Газета мечети Джамиг",
        verbose_name="Название газеты",
        help_text="Выводится крупно в шапке-мачте каждого номера (сайт и печать).",
    )
    tagline = models.CharField(
        max_length=300,
        blank=True,
        default="Весть мечети Джамиг",
        verbose_name="Девиз / подзаголовок",
        help_text="Небольшая строка под названием газеты (необязательно).",
    )
    address = models.CharField(
        max_length=300,
        blank=True,
        verbose_name="Адрес и контакты",
        help_text="Например: г. Казань, ул. ..., тел. ... — печатается в выходных данных.",
    )
    founder = models.CharField(
        max_length=300,
        blank=True,
        verbose_name="Учредитель",
        help_text="Например: Местная религиозная организация «Мечеть Джамиг».",
    )
    print_pages = models.PositiveIntegerField(
        default=0,
        verbose_name="Полос в номере",
        help_text=(
            "Сколько сторон листа занимает газета (4, 8, 12, 16...). "
            "0 — определять автоматически по объёму материалов. "
            "Если число не кратно 4, оно округляется вверх — иначе при "
            "складывании листов остаются пустые страницы."
        ),
    )

    class Meta:
        verbose_name = "Настройки газеты"
        verbose_name_plural = "Настройки газеты"

    def save(self, *args, **kwargs):
        """Храним ровно одну запись настроек (pk всегда = 1)."""
        self.pk = 1
        if self.print_pages:
            self.print_pages = max(4, (self.print_pages // 4 + 1) * 4)
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return self.publication_name


class NewspaperIssue(models.Model):
    """Выпуск газеты мечети (электронная версия печатной газеты)"""

    STATUS_CHOICES = (
        ("draft", "Черновик"),
        ("published", "Опубликовано"),
        ("archived", "В архиве"),
    )

    title = models.CharField(
        max_length=200,
        verbose_name="Тема номера",
        help_text="Краткое название этого выпуска (например: «Рамадан 1447»).",
    )
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

    # ---------- АВТОМАТИЧЕСКИЙ АНОНС (по первой полосе) ----------

    @property
    def front_page_blocks(self):
        """Блоки, помеченные как «первая полоса» (или первые по порядку)."""
        blocks = list(self.blocks.all())  # related_name динамический для Pylance
        front = [b for b in blocks if b.is_front_page]
        return front or blocks[:1]

    @property
    def announce_image(self):
        """Главное фото анонса: обложка, иначе первое фото первой полосы."""
        if self.cover_image:
            return self.cover_image
        for block in self.front_page_blocks:
            if block.photo:
                return block.photo
            gallery = block.get_gallery_images()
            if gallery:
                return gallery[0]
        return None

    @property
    def announce_headline(self):
        """Главный заголовок анонса: первая полоса, самый крупный материал."""
        lead = None
        for block in self.front_page_blocks:
            if not block.title:
                continue
            if lead is None or block.size_weight > lead.size_weight:
                lead = block
        if lead is not None:
            return lead.title
        return self.title

    @property
    def announce_text(self):
        """Текст анонса: явное поле description, иначе лид первой полосы."""
        if self.description:
            return self.description
        for block in self.front_page_blocks:
            if block.subtitle:
                return block.subtitle
        for block in self.front_page_blocks:
            plain = block.get_lead_paragraph()
            if plain:
                return plain
        return ""

    def clean(self):
        """Проверяет PDF-файл: только формат PDF."""
        super().clean()
        if self.pdf_file:
            name = getattr(self.pdf_file, "name", "") or ""
            ext = os.path.splitext(name)[1].lower()
            content_type = getattr(self.pdf_file, "content_type", None)
            if ext and ext != ".pdf":
                raise ValidationError({"pdf_file": "Можно загружать только файлы в формате PDF."})
            if content_type and content_type not in ("application/pdf",):
                raise ValidationError({"pdf_file": "Можно загружать только файлы в формате PDF."})

    # ---------- ПЕЧАТНАЯ ВЁРСТКА (полосы для типографии) ----------

    @property
    def publication_name(self):
        """Название газеты из общих настроек (редактируется редакторами)."""
        try:
            return NewspaperSettings.load().publication_name
        except Exception:
            return "Газета мечети Джамиг"

    @property
    def print_pages(self):
        """Число полос (сторон) номера — кратно 4 для шитья листов степлером.

        0 в настройках = автораскладка: полос берётся ровно столько, сколько
        нужно по объёму материалов (минимум 4). Явное значение из настроек
        всегда respected — оно может быть и БОЛЬШЕ нужного (редактор хочет
        номер фиксированной полосности), но никогда не меньше, чем требует
        контент: иначе материалы «сваливаются» на одну полосу и остаются
        пустые страницы.
        """
        try:
            pages = NewspaperSettings.load().print_pages or 0
        except Exception:
            pages = 0
        if pages < 4:
            return 0  # авто
        return pages if pages % 4 == 0 else (pages // 4 + 1) * 4

    _PAGE_CAPACITY = {
        "lead": 2600,
        "large": 1800,
        "normal": 1300,
        "small": 900,
        "ad": 1000,
    }

    def estimate_block_height_mm(self, block):
        """Оценка высоты материала в мм ОДНОЙ КОЛОНКИ полосы.

        Используется для автоматической раскладки печатной версии: число полос
        и распределение материалов по ним нужно посчитать заранее, чтобы не
        оставлять пустых страниц. Колонка печатной полосы — 2 колонки шириной
        ~90 мм (в ~1.5 раза уже прежней), поэтому строка ≈ 85 знаков.
        """
        text = re.sub(r"<[^>]+>", " ", block.content or "")
        chars = len(text.strip())
        # ~85 знаков в строке широкой газетной колонки, ~4.7 мм на строку
        mm = (chars / 85.0) * 4.7
        if block.photo:
            # Фото на всю колонку занимает много места; узкое фото (текст
            # обтекает) добавляет к высоте только часть своей высоты.
            full_h = 95 if block.size in ("lead", "large") else 60
            frac = {"full": 1.0, "half": 0.5, "third": 0.34}.get(
                block.photo_width, 1.0
            )
            mm += full_h * frac
        mm += len(block.print_gallery or []) * 55
        if block.subtitle:
            mm += 10
        if block.author_name:
            mm += 6
        return max(25.0, mm)

    def build_print_pages(self):
        """Разливает материалы конструктора по печатным полосам (сторонам).

        Каждая полоса — ровно одна половина разворота A3: 2 колонки шириной
        ~90 мм и высотой ~250 мм (ёмкость полосы ~500 мм колоночного текста).
        Число полос: минимум 4; если задано вручную в настройках — не меньше
        этого числа; но всегда достаточно, чтобы ВЕСЬ контент разместился без
        переполнения и без пустых страниц. Кратно 4 (шитьё степлером).
        """
        blocks = list(self.blocks.all().order_by("order", "id"))  # type: ignore[attr-defined]
        page_cap = 500.0  # мм колоночной высоты на одну полосу (2 × 250)

        front = [b for b in blocks if b.is_front_page]
        rest = [b for b in blocks if not b.is_front_page]
        page1 = front or rest[:1]
        pool = rest[1:] if (not front and page1) else rest

        heights = {b.pk: self.estimate_block_height_mm(b) for b in blocks}
        total_h = sum(heights[b.pk] for b in blocks) or page_cap

        needed = -(-int(total_h) // int(page_cap)) or 1  # ceil
        pages_count = max(4, needed)
        if self.print_pages:  # явная полосность из настроек
            pages_count = max(pages_count, self.print_pages)
        if pages_count % 4:
            pages_count = ((pages_count + 3) // 4) * 4

        ordered = list(page1) + list(pool)
        per_cap = max(total_h / pages_count, 1.0)
        pages: list[list] = [[] for _ in range(pages_count)]
        idx, acc = 0, 0.0
        for b in ordered:
            h = heights[b.pk]
            # Полоса уже с контентом и следующий блок её переполнит —
            # переходим к следующей полосе. Последний блок всегда остаётся
            # на последней полосе (там же выходные данные) — браузер/принтер
            # разобьёт его по колонкам.
            if idx < pages_count - 1 and acc > 0 and acc + h > per_cap:
                idx += 1
                acc = 0.0
            pages[idx].append(b)
            acc += h
        return pages

    def build_print_sheets(self):
        """Собирает физические листы A3 для двусторонней печати «книжкой».

        Возвращает список листов; каждый лист — это [левая_половина,
        правая_половина], где половина — dict с номером полосы, её
        материалами и флагами ``is_front`` / ``is_last``.

        Порядок spread-фольги (как в типографии):
          сторона 1 листа: полоса 1 (титул) | полоса N (задняя обложка)
          сторона 2 листа: полоса N-1       | полоса 2
        После складывания и шитья степлером страницы идут 1..N по порядку.
        """
        pages = self.build_print_pages()
        n = len(pages)
        order = []  # попарно: (левая, правая) для каждой стороны листа
        lo, hi = 0, n - 1
        left_first = True
        while lo <= hi:
            pair = (lo, hi) if left_first else (hi, lo)
            order.append(pair)
            left_first = not left_first
            lo += 1
            hi -= 1
        sheets = []
        for side in order:
            halves = []
            for idx in side:
                halves.append(
                    {
                        "page_no": idx + 1,
                        "blocks": pages[idx],
                        "is_front": idx == 0,
                        "is_last": idx == n - 1,
                    }
                )
            sheets.append(halves)
        return sheets

    def colophon_lines(self):
        """Выходные данные для последней полосы печатной версии."""
        lines = [f"«{self.publication_name}»"]
        if self.founder_from_settings:
            lines.append(f"Учредитель: {self.founder_from_settings}")
        editor_name = self.editor.get_full_name() if self.editor else ""
        if editor_name:
            lines.append(f"Редактор: {editor_name}")
        if self.address_from_settings:
            lines.append(self.address_from_settings)
        lines.append(f"№ {self.number} от {self.issue_date.strftime('%d.%m.%Y')}")
        lines.append("Подготовлено в электронном конструкторе газеты.")
        return lines

    @property
    def founder_from_settings(self):
        try:
            return NewspaperSettings.load().founder
        except Exception:
            return ""

    @property
    def address_from_settings(self):
        try:
            return NewspaperSettings.load().address
        except Exception:
            return ""

    def __str__(self):
        """Строковое представление выпуска: номер и название."""
        return f"{self.number} — {self.title}"


BLOCK_TYPES = (
    ("article", "Статья"),
    ("interview", "Интервью"),
    ("news", "Заметка"),
    ("photo", "Фоторепортаж"),
    ("announcement", "Объявление"),
    ("ad", "Реклама"),
)

BLOCK_SIZES = (
    ("lead", "Главная (первый экран, крупный шрифт)"),
    ("large", "Крупная статья"),
    ("normal", "Обычная"),
    ("small", "Заметка в колонку"),
)


def validate_image_format(image):
    """Проверяет, что загруженный файл является изображением."""
    from PIL import Image

    try:
        image.seek(0)
        image.verify()
    except Exception:
        raise ValidationError(
            "Файл не является изображением. Поддерживаются JPG, PNG, WEBP."
        )


class NewspaperBlock(models.Model):
    """Блок (материал) выпуска газеты: заголовок, текст, фото.

    Из блоков конструктора собирается классическая газетная вёрстка:
    заголовок, подзаголовок, автор, главное фото с подписью, галерея,
    текст с выделенными секциями и цитатами.
    """

    title = models.CharField(max_length=250, verbose_name="Заголовок")
    subtitle = models.CharField(
        max_length=350, blank=True, verbose_name="Подзаголовок"
    )
    block_type = models.CharField(
        max_length=20, choices=BLOCK_TYPES, default="article", verbose_name="Тип блока"
    )
    size = models.CharField(
        max_length=10,
        choices=BLOCK_SIZES,
        default="normal",
        verbose_name="Размер в вёрстке",
    )
    content = models.TextField(
        blank=True,
        verbose_name="Текст",
        help_text=(
            "Абзацы — с новой строки. Дополнительные возможности разметки:\n"
            "## Заголовок секции — крупный подзаголовок внутри материала;\n"
            "### Подзаголовок — обычный подзаголовок секции;\n"
            "> Текст — врезка-цитата; --- — разделительная линия."
        ),
    )
    author_name = models.CharField(
        max_length=150, blank=True, verbose_name="Автор материала"
    )
    photo = models.ImageField(
        upload_to="newspaper/blocks/%Y/%m/",
        blank=True,
        verbose_name="Главное фото",
        validators=[validate_image_format],
    )
    photo_caption = models.CharField(
        max_length=300, blank=True, verbose_name="Подпись к фото"
    )
    PHOTO_WIDTH_CHOICES = (
        ("full", "На всю колонку"),
        ("half", "Половина колонки (текст обтекает)"),
        ("third", "Треть колонки (текст обтекает)"),
    )
    photo_width = models.CharField(
        max_length=10,
        choices=PHOTO_WIDTH_CHOICES,
        default="full",
        verbose_name="Ширина фото",
        help_text=(
            "Если выбрать «половину» или «треть» — текст будет обтекать фото, "
            "как в печатной газете."
        ),
    )
    gallery = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Галерея фотографий",
        help_text="Список [{'image': path, 'caption': подпись}] — заполняется в конструкторе.",
    )
    is_front_page = models.BooleanField(
        default=False,
        verbose_name="Первая полоса",
        help_text="Материал участвует в формировании анонса на главной странице.",
    )

    # ---------- РЕКЛАМА ----------
    advertiser_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Рекламодатель",
        help_text="Название организации или ФИО (для рекламных материалов).",
    )
    advertiser_contact = models.CharField(
        max_length=300,
        blank=True,
        verbose_name="Контакты рекламодателя",
        help_text="Телефон, адрес, сайт — печатаются под объявлением.",
    )
    ad_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Стоимость размещения, ₽",
    )
    ad_paid = models.BooleanField(
        default=False,
        verbose_name="Оплачено",
        help_text="Отметьте, когда реклама оплачена — неоплаченные объявления в печать не попадают.",
    )
    ad_discount = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Скидка, %",
    )
    ad_volume = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Объём объявления",
        help_text="Например: 1/8 полосы, 1/4 полосы, строка.",
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

    @property
    def size_weight(self):
        """Вес размера блока (для выбора главного заголовка анонса)."""
        weights = {"lead": 3, "large": 2, "normal": 1, "small": 0}
        return weights.get(self.size, 1)

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

    # ---------- ФОТО ----------

    def get_gallery_images(self):
        """Возвращает список {'url', 'caption'} дополнительных фото блока."""
        items = []
        raw = self.gallery or []
        if isinstance(raw, dict):  # защита от неверного формата
            raw = raw.get("images", [])
        for item in raw:
            if not isinstance(item, dict):
                continue
            path = item.get("image") or item.get("url")
            if not path:
                continue
            url = path if str(path).startswith(("http://", "https://", "/media/")) else f"/media/{path}"
            items.append({"url": url, "caption": item.get("caption", "")})
        return items

    # ---------- РАЗМЕТКА ТЕКСТА ----------

    _HTML_TAG_RE = re.compile(r"<[^>]+>")

    def get_content_html(self):
        """Возвращает текст блока в виде HTML-абзацев с газетной разметкой.

        Поддерживается безопасная inline-разметка (<b>, <i>, <strong>, <em>,
        <a href>, <u>) и блочные маркеры: ## / ### (секции), > (цитата),
        --- (разделитель).
        """
        if not self.content:
            return ""
        allowed_tags = {
            "b", "i", "strong", "em", "u", "s", "span", "br", "a",
            "h2", "h3", "blockquote", "p", "hr", "ul", "ol", "li",
        }
        cleaned = self._strip_unsafe_tags(self.content, allowed_tags)
        # Пустые строки-маркеры ("### " / "> ") после strip() превращаются в
        # "###"/">" — считаем их обычным текстом, а не заголовком/цитатой.
        parts = []
        for line in cleaned.split("\n"):
            line = line.strip()
            if not line:
                continue
            if line.startswith("### "):
                parts.append(f"<h4 class='news-section-sub'>{line[4:]}</h4>")
            elif line.startswith("## "):
                parts.append(f"<h3 class='news-section-title'>{line[3:]}</h3>")
            elif line.startswith("# "):
                parts.append(f"<h3 class='news-section-title'>{line[2:]}</h3>")
            elif line.startswith("> "):
                parts.append(f"<blockquote class='news-quote'>{line[2:]}</blockquote>")
            elif set(line) <= {"-", "—", "*"} and len(line) >= 3:
                parts.append("<hr class='news-rule'>")
            else:
                parts.append(f"<p>{line}</p>")
        return "".join(parts)

    @classmethod
    def _strip_unsafe_tags(cls, text, allowed_tags):
        """Удаляет теги, не входящие в белый список, и опасные атрибуты."""
        text = re.sub(r"(?i)<\s*(script|style|iframe|object|embed)[^>]*>.*?<\s*/\s*\1\s*>", "", text, flags=re.S)

        def replace_tag(match):
            closing = match.group(1) == "/"
            tag = match.group(2).lower()
            attrs = match.group(3) or ""
            if tag not in allowed_tags:
                return ""
            if tag == "a":
                href_match = re.search(r"(?i)href\s*=\s*[\"']?([^\"'\s>]+)", attrs)
                href = href_match.group(1) if href_match else ""
                if href.startswith(("http://", "https://", "/", "mailto:")):
                    return f'<a href="{href}" target="_blank" rel="noopener noreferrer">' + ("" if closing else "")
                return ""
            return f"</{tag}>" if closing else f"<{tag}>"

        return re.sub(r"<\s*(/?)\s*([a-zA-Z0-9]+)((?:\s+[^<>]*)?)/?>", replace_tag, text)

    def get_lead_paragraph(self, max_length=220):
        """Возвращает первый текстовый абзац блока plain-текстом (для анонса)."""
        for line in (self.content or "").split("\n"):
            line = line.strip()
            if not line or set(line) <= {"-", "—", "*"}:
                continue
            if line.startswith(("#", ">")):
                continue
            plain = re.sub(r"<[^>]+>", "", line).strip()
            if len(plain) > max_length:
                plain = plain[:max_length].rsplit(" ", 1)[0] + "…"
            return plain
        return ""

    # ---------- ПЕЧАТНАЯ ВЕРСИЯ (PDF для типографии) ----------

    _PRINT_CLASS_MAP = {
        "news-section-title": "print-section-title",
        "news-section-sub": "print-section-sub",
        "news-quote": "print-quote",
        "news-rule": "print-rule",
    }

    @property
    def print_content_parts(self):
        """HTML текста материала с классами печатного шаблона (для WeasyPrint)."""
        html = self.get_content_html()
        for old_cls, new_cls in self._PRINT_CLASS_MAP.items():
            html = html.replace(f"class='{old_cls}'", f'class="{new_cls}"')
        return html

    @property
    def print_photo_url(self):
        """Путь фото для WeasyPrint: base_url = MEDIA_ROOT, поэтому без /media/."""
        if not self.photo:
            return ""
        url = self.photo.url
        return url.removeprefix(settings.MEDIA_URL).lstrip("/")

    @property
    def print_gallery(self):
        """Галерея фото с относительными путями — WeasyPrint резолвит их от MEDIA_ROOT."""
        items = []
        for item in self.get_gallery_images():
            url = item["url"]
            if url.startswith("/media/"):
                url = url[len("/media/"):]
            items.append({"url": url, "caption": item["caption"]})
        return items

    @property
    def is_ad(self):
        """Материал является рекламным объявлением."""
        return self.block_type == "ad"

    @property
    def ad_final_price(self):
        """Итоговая стоимость рекламы со скидкой (для учёта в конструкторе)."""
        if self.ad_price is None:
            return None
        if self.ad_discount:
            return self.ad_price * (100 - self.ad_discount) / 100
        return self.ad_price

    def __str__(self):
        """Строковое представление блока: его заголовок."""
        return self.title