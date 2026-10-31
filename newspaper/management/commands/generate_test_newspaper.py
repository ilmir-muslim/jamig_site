"""Генерация тестовой газеты, покрывающей весь функционал приложения newspaper.
Запуск:
    python manage.py generate_test_newspaper

Что создаётся:
* тестовый редактор газеты (если его ещё нет);
* выпуск №1 «Опубликовано»: все типы блоков, все размеры, разметка текста,
  фото, галереи, PDF, обложка, автоматический анонс;
* выпуск №2 «Опубликовано»: ручной анонс (description заполнен вручную);
* выпуск №3 «Черновик» и выпуск №4 «В архиве» — проверка статусов.
Повторный запуск безопасен: старые тестовые выпуски (номер начинается с «Тест»)
удаляются вместе со своими файлами, затем создаются заново.
"""

from __future__ import annotations

import io
from contextlib import suppress
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import SuspiciousFileOperation
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont

from newspaper.models import NewspaperBlock, NewspaperIssue, NewspaperSettings

User = get_user_model()
TEST_NUMBER_PREFIX = "Тест"
EDITOR_EMAIL = "newspaper-editor@example.com"
EDITOR_PASSWORD = "editor12345"
GALLERY_TEST_DIR = "newspaper/gallery/__test__"

# Минимальный корректный PDF (одна пустая страница) — только для проверки поля.
MINIMAL_PDF = b"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] >> endobj
trailer << /Root 1 0 R >>
%%EOF
"""


# ---------- ЗАГЛУШКИ ИЗОБРАЖЕНИЙ ----------
def _get_font(size: int = 42):
    """Шрифт для подписи на заглушке (насколько позволяет Pillow)."""
    try:
        return ImageFont.load_default(size=size)  # Pillow >= 10.1
    except TypeError:
        return ImageFont.load_default()


def make_image_file(
    name: str,
    color: tuple[int, int, int],
    label: str,
    size: tuple[int, int] = (1200, 800),
) -> ContentFile:
    """Рисует цветную заглушку с рамкой, диагоналями и подписью."""
    img = Image.new("RGB", size, color)
    draw = ImageDraw.Draw(img)
    w, h = size
    draw.rectangle([12, 12, w - 12, h - 12], outline="white", width=6)
    draw.line([(0, 0), (w, h)], fill=(255, 255, 255), width=3)
    draw.line([(w, 0), (0, h)], fill=(255, 255, 255), width=3)
    font = _get_font()
    bbox = draw.textbbox((0, 0), label, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((w - tw) / 2, (h - th) / 2), label, fill="white", font=font)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return ContentFile(buf.getvalue(), name=name)


def make_gallery(
    slug: str, specs: list[tuple[tuple[int, int, int], str]]
) -> list[dict]:
    """Сохраняет набор фото в MEDIA и возвращает JSON-список для поля gallery."""
    items = []
    for i, (color, caption) in enumerate(specs, start=1):
        name = f"{slug}_g{i}.jpg"
        rel_path = default_storage.save(
            f"{GALLERY_TEST_DIR}/{name}",
            make_image_file(name, color, f"Галерея {i}"),
        )
        items.append({"image": rel_path, "caption": caption})
    return items


# ---------- ВСПОМОГАТЕЛЬНОЕ ----------
def get_or_create_editor():
    """Создаёт тестового редактора газеты (или возвращает существующего)."""
    editor, created = User.objects.get_or_create(
        email=EDITOR_EMAIL,
        defaults={
            "user_type": "newspaper_editor",
            "first_name": "Тестовый",
            "last_name": "Редактор",
            "is_verified": True,
        },
    )
    if created:
        editor.set_password(EDITOR_PASSWORD)
        editor.save(update_fields=["password"])
    return editor, created


def delete_issue_files(issue: NewspaperIssue) -> None:
    """Удаляет медиафайлы выпуска (обложка, PDF, фото и галереи блоков)."""
    for block in issue.blocks.all():  # type: ignore[attr-defined]
        if block.photo:
            block.photo.delete(save=False)
        for item in block.gallery or []:
            path = item.get("image") if isinstance(item, dict) else None
            if path:
                with suppress(OSError, SuspiciousFileOperation):
                    if default_storage.exists(path):
                        default_storage.delete(path)
    if issue.cover_image:
        issue.cover_image.delete(save=False)
    if issue.pdf_file:
        issue.pdf_file.delete(save=False)


def cleanup_old_test_issues() -> int:
    """Удаляет ранее сгенерированные тестовые выпуски."""
    old_issues = NewspaperIssue.objects.filter(number__startswith=TEST_NUMBER_PREFIX)
    count = old_issues.count()
    for issue in old_issues:
        delete_issue_files(issue)
        issue.delete()  # блоки удалятся каскадно
    return count


def add_block(
    issue: NewspaperIssue,
    photo: tuple[str, tuple[int, int, int]] | None = None,
    gallery_specs: list[tuple[tuple[int, int, int], str]] | None = None,
    **fields,
) -> NewspaperBlock:
    """Создаёт блок выпуска; при необходимости прикрепляет фото и галерею."""
    block = NewspaperBlock(issue=issue, **fields)
    if photo:
        file_name, color = photo
        block.photo.save(
            file_name, make_image_file(file_name, color, "Главное фото"), save=False
        )
    if gallery_specs is not None:
        block.gallery = make_gallery(issue.slug or "issue", gallery_specs)
    block.save()
    return block


# ---------- ТЕКСТЫ (демонстрация всей разметки) ----------
LEAD_ARTICLE_CONTENT = """Первый абзац (лид) главной статьи номера. Именно из него формируется автоматический анонс выпуска, если анонс не заполнен вручную.
## Крупная секция статьи
Это маркер «##» — крупный подзаголовок внутри материала. После него продолжается основной текст статьи.
### Обычный подзаголовок секции
Это маркер «###» — подзаголовок поменьше. Удобно структурировать длинные материалы.
> «Это врезка-цитата. Она оформляется отдельным блоком и выделяется в газетной вёрстке.»
---
Финальный абзац с проверкой встроенной разметки: <b>жирный текст</b>, <i>курсив</i>, <strong>усиленное выделение</strong>, <em>акцент</em>, <u>подчёркнутый текст</u>, <s>зачёркнутый текст</s>, внешняя <a href="https://example.com">ссылка</a> и почтовая <a href="mailto:info@example.com">ссылка mailto</a>."""

INTERVIEW_CONTENT = """<b>— Расскажите, как давно существует газета мечети?</b>
Первый номер вышел ещё в начале двухтысячных: тогда это был двустраничный листок объявлений, который раздавали после пятничной молитвы.
<b>— Что изменилось с появлением электронной версии?</b>
Теперь выпуск читают не только прихожане, но и жители других городов. Мы сохранили классическую газетную вёрстку, но добавили фотогалереи и удобную навигацию по полосам.
> «Газета — это не просто новости, это летопись общины», — отмечает собеседник.
<b>— Какие планы на следующий год?</b>
Запустить молодёжную рубрику и расширить раздел интервью. Редакция всегда открыта для новых авторов.
---
Редакция благодарит собеседника за уделённое время."""

PHOTO_REPORT_CONTENT = """Короткий вводный текст фоторепортажа. Основная нагрузка в этом формате — галерея фотографий: пролистайте её под текстом.
Все снимки сделаны на прошедших выходных во время мероприятия при мечети."""

MARKUP_ARTICLE_CONTENT = """Материал для проверки всех элементов разметки текста. Первый абзац всегда становится лид-текстом.
## Первая секция
Абзац внутри первой секции. Новый абзац начинается просто с новой строки.
### Внутри секции есть подраздел
> Врезка-цитата посреди материала.
---
## Вторая секция
Текст после разделительной линии со <strong>встроенной</strong> разметкой: <b>жирный</b>, <i>курсив</i>, <em>акцент</em>, <u>подчёркнутый</u>, <s>зачёркнутый</s> и <a href="https://example.com">ссылка</a>."""

NEWS_NOTE_1 = """Короткая заметка в колонку. Формат «новости» подходит для оперативных сообщений: расписание, объявления, краткие итоги событий.
Второй абзац заметки."""

NEWS_NOTE_2 = """Ещё одна небольшая заметка без фотографии — проверяем, как выглядит блок в полную ширину полосы без иллюстраций."""

ANNOUNCEMENT_CONTENT = """Приглашаем всех желающих на осенний субботник при мечети.
### Когда
Суббота, 14 ноября, начало в 10:00.
### Где
Двор мечети, вход со стороны парковки.
> Пожалуйста, приходите в удобной одежде — инвентарь выдадим на месте.
---
Вопросы по телефону: <b>+7 (999) 000-00-00</b>."""

GREEN = (46, 125, 50)
BLUE = (21, 101, 192)
ORANGE = (239, 108, 0)
PURPLE = (106, 27, 154)
TEAL = (0, 121, 107)
RED = (198, 40, 40)


def _fill_pages_with_extra_blocks(issue: NewspaperIssue, target_pages: int) -> None:
    """
    Добавляет дополнительные материалы (заметки), чтобы выпуск
    занимал примерно target_pages полос согласно настройкам.
    """
    current_blocks_count = issue.blocks.count()  # type: ignore[attr-defined]

    # Эвристическая оценка: сколько блоков нужно на одну полосу.
    blocks_per_page_estimate = 4
    needed_total_blocks = target_pages * blocks_per_page_estimate

    if current_blocks_count >= needed_total_blocks:
        return

    extra_needed = needed_total_blocks - current_blocks_count
    colors = [GREEN, BLUE, ORANGE, PURPLE, TEAL, RED]

    for i in range(extra_needed):
        color = colors[i % len(colors)]
        add_block(
            issue,
            photo=(f"extra_block_{i}.jpg", color),
            title=f"Дополнительная заметка для заполнения полосы {i + 1}",
            subtitle="Тестовый материал для проверки вёрстки",
            block_type="news",
            size="small",
            content=f"Это дополнительный материал #{i + 1}, созданный автоматически, чтобы убедиться, что газета занимает заданное количество полос ({target_pages}). Текст может быть любым.",
            author_name="Автоматический редактор",
            order=current_blocks_count + i + 1,
        )


# ---------- СОЗДАНИЕ ВЫПУСКОВ ----------
@transaction.atomic
def build_issue_one(editor, today) -> NewspaperIssue:
    """Выпуск №1: опубликован, авто-анонс, все типы блоков и размеров, фото, галереи, PDF."""
    issue = NewspaperIssue(
        title="Полный тест разметки и вёрстки",
        number="Тест №1 (991)",
        issue_date=today,
        status="published",
        editor=editor,
    )
    issue.cover_image.save(
        "test_cover_1.jpg",
        make_image_file("test_cover_1.jpg", BLUE, "Обложка №1"),
        save=False,
    )
    issue.pdf_file.save(
        "test_issue_1.pdf",
        ContentFile(MINIMAL_PDF, name="test_issue_1.pdf"),
        save=False,
    )
    issue.save()

    add_block(
        issue,
        photo=("lead_photo.jpg", GREEN),
        gallery_specs=[
            (ORANGE, "Подпись к первому фото галереи"),
            (TEAL, "Второй снимок мероприятия"),
            (PURPLE, "Третий снимок — общий план"),
        ],
        title="Главная статья номера: жизнь общины",
        subtitle="Итоги месяца и планы на будущее",
        block_type="article",
        size="lead",
        content=LEAD_ARTICLE_CONTENT,
        author_name="Ильдар Хасанов",
        photo_caption="Прихожане после пятничной молитвы. Фото: редакция",
        is_front_page=True,
        order=1,
    )
    add_block(
        issue,
        photo=("interview_photo.jpg", PURPLE),
        title="Интервью с имамом: «Газета — летопись общины»",
        subtitle="Беседа с настоятелем о печатной и электронной версии",
        block_type="interview",
        size="large",
        content=INTERVIEW_CONTENT,
        author_name="Алия Сафина",
        photo_caption="Настоятель мечети во время беседы",
        is_front_page=True,
        order=2,
    )
    add_block(
        issue,
        gallery_specs=[
            (BLUE, "Открытие мероприятия"),
            (GREEN, "Экскурсия для гостей"),
            (ORANGE, "Детская программа"),
            (RED, "Завершение вечера"),
        ],
        title="Фоторепортаж: выходные при мечети",
        block_type="photo",
        size="large",
        content=PHOTO_REPORT_CONTENT,
        author_name="Фотослужба мечети",
        order=3,
    )
    add_block(
        issue,
        title="Проверка всех элементов разметки текста",
        subtitle="Секции, цитаты, разделители и встроенные теги",
        block_type="article",
        size="normal",
        content=MARKUP_ARTICLE_CONTENT,
        author_name="Тестовый Автор",
        order=4,
    )
    add_block(
        issue,
        photo=("news_photo.jpg", TEAL),
        title="Заметка: расписание занятий на неделю",
        block_type="news",
        size="small",
        content=NEWS_NOTE_1,
        photo_caption="Учебный класс мечети",
        order=5,
    )
    add_block(
        issue,
        title="Заметка без фотографии",
        block_type="news",
        size="small",
        content=NEWS_NOTE_2,
        order=6,
    )
    add_block(
        issue,
        title="Объявление: осенний субботник",
        block_type="announcement",
        size="small",
        content=ANNOUNCEMENT_CONTENT,
        order=7,
    )

    # Заполнение полос согласно настройкам
    settings_obj = NewspaperSettings.load()
    _fill_pages_with_extra_blocks(issue, settings_obj.print_pages)

    return issue


@transaction.atomic
def build_issue_two(editor, today) -> NewspaperIssue:
    """Выпуск №2: опубликован, ручной анонс (description задан вручную)."""
    issue = NewspaperIssue(
        title="Ручной анонс выпуска",
        number="Тест №2 (990)",
        issue_date=today - timedelta(days=7),
        status="published",
        editor=editor,
        description=(
            "Этот анонс написан вручную редактором: он используется вместо "
            "автоматической выжимки из первой полосы."
        ),
    )
    issue.cover_image.save(
        "test_cover_2.jpg",
        make_image_file("test_cover_2.jpg", TEAL, "Обложка №2"),
        save=False,
    )
    issue.save()
    add_block(
        issue,
        title="Статья второго выпуска",
        subtitle="Проверяем ручной анонс на главной странице",
        block_type="article",
        size="normal",
        content="Текст статьи второго выпуска. Анонс на главной должен показывать не этот лид, а текст, который редактор ввёл вручную в поле «Анонс».",
        author_name="Редактор газеты",
        is_front_page=True,
        order=1,
    )
    add_block(
        issue,
        title="Короткая заметка второго выпуска",
        block_type="news",
        size="small",
        content="Небольшая заметка для проверки вёрстки выпуска из двух материалов.",
        order=2,
    )

    # Заполнение полос согласно настройкам
    settings_obj = NewspaperSettings.load()
    _fill_pages_with_extra_blocks(issue, settings_obj.print_pages)

    return issue


@transaction.atomic
def build_issue_three(editor, today) -> NewspaperIssue:
    """Выпуск №3: черновик — не должен отображаться в публичном архиве."""
    issue = NewspaperIssue(
        title="Черновик для проверки статуса",
        number="Тест №3 (989)",
        issue_date=today - timedelta(days=14),
        status="draft",
        editor=editor,
    )
    issue.save()
    add_block(
        issue,
        title="Материал в черновике",
        block_type="article",
        size="normal",
        content="Этот выпуск имеет статус «Черновик»: его видят только редакторы в конструкторе.",
        order=1,
    )
    return issue


@transaction.atomic
def build_issue_four(editor, today) -> NewspaperIssue:
    """Выпуск №4: архив — не должен отображаться в публичном архиве."""
    issue = NewspaperIssue(
        title="Архивный номер",
        number="Тест №4 (988)",
        issue_date=today - timedelta(days=30),
        status="archived",
        editor=editor,
    )
    issue.save()
    add_block(
        issue,
        title="Материал архивного номера",
        block_type="article",
        size="normal",
        content="Этот выпуск имеет статус «В архиве» и скрыт из публичного списка.",
        order=1,
    )
    return issue


# ---------- КОМАНДА ----------
class Command(BaseCommand):
    help = "Генерирует тестовые выпуски газеты, покрывающие весь функционал приложения."

    def handle(self, *args, **options):
        today = timezone.localdate()
        editor, editor_created = get_or_create_editor()
        removed = cleanup_old_test_issues()
        if removed:
            self.stdout.write(
                self.style.WARNING(f"Удалено старых тестовых выпусков: {removed}")
            )

        issue1 = build_issue_one(editor, today)
        issue2 = build_issue_two(editor, today)
        issue3 = build_issue_three(editor, today)
        issue4 = build_issue_four(editor, today)

        self.stdout.write(self.style.SUCCESS("\nТестовая газета сгенерирована.\n"))
        if editor_created:
            self.stdout.write("Редактор газеты:")
            self.stdout.write(f"  email:    {EDITOR_EMAIL}")
            self.stdout.write(f"  пароль:   {EDITOR_PASSWORD}\n")
        else:
            self.stdout.write(f"Использован существующий редактор: {EDITOR_EMAIL}\n")

        self.stdout.write("Выпуски:")
        for issue in (issue1, issue2, issue3, issue4):
            blocks = issue.blocks.count()  # type: ignore[attr-defined]
            url = issue.get_absolute_url() if issue.status == "published" else "(скрыт)"
            status_label = issue.get_status_display()  # type: ignore[attr-defined]
            self.stdout.write(
                f"  [{status_label}] {issue.number} — «{issue.title}» "
                f"| блоков: {blocks} | {url}"
            )

        self.stdout.write("\nЧто проверить:")
        self.stdout.write(
            "  * /newspaper/                — архив: видны только выпуски 1 и 2;"
        )
        self.stdout.write(
            f"  * {issue1.get_absolute_url()} — вёрстка всех блоков, галереи, цитаты, секции;"
        )
        self.stdout.write(
            "  * главная страница           — авто-анонс выпуска 1 и ручной анонс выпуска 2;"
        )
        self.stdout.write(
            "  * /newspaper/editor/         — конструктор: черновик и архив, редактирование;"
        )
        self.stdout.write("  * PDF доступен на странице выпуска 1.")
