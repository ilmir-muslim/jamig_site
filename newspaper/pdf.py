"""Экспорт выпуска газеты в PDF (печатная версия для типографии).

Генерация выполняется через WeasyPrint из отдельного печатного шаблона
``templates/newspaper/issue_print.html``: формат A3 альбомный — классическая
складная газета, колонки, засечные шрифты, обрыв текста по колонкам.

Шрифт Tahoma задан как основной, но WeasyPrint использует его только если
шрифт установлен в системе (Windows). На Linux он автоматически заменится
на доступный serif-шрифт (DejaVu Serif и т.п.), поэтому верстка не сломается.
"""

from django.conf import settings as django_settings
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.utils import timezone

from .models import NewspaperSettings


def build_issue_pdf(issue) -> bytes:
    """Рендерит выпуск газеты в PDF и возвращает байты документа.

    Полосы формируются в spread-порядке для двусторонней печати с креплением
    листов степлером («вложенные листы», как книга): на одном физическом листе
    A3 с двух сторон печатаются полосы [1, N], [N-1, 2], [N-2, 3] и т.д. —
    после складывания и шитья страницы идут по порядку 1..N без пустых мест.
    """
    from weasyprint import HTML  # импорт здесь: модуль опционален для окружения

    try:
        settings_obj = NewspaperSettings.load()
    except Exception:
        settings_obj = None
    html = render_to_string(
        "newspaper/issue_print.html",
        {
            "issue": issue,
            "sheets": issue.build_print_sheets(),
            "total_pages": len(issue.build_print_pages()),
            "colophon": issue.colophon_lines(),
            "settings_tagline": settings_obj.tagline if settings_obj else "",
            "generated_at": timezone.localtime(),
        },
    )
    # base_url = MEDIA_ROOT. WeasyPrint резолвит "/media/..." в
    # MEDIA_ROOT + "/media/...", чего по умолчанию нет, поэтому на лету
    # создаём симлинк MEDIA_ROOT/media -> MEDIA_ROOT (нужно только для
    # серверного PDF; печать из браузера использует юрку /media/ напрямую).
    media_root_path = django_settings.MEDIA_ROOT
    media_root = str(media_root_path)
    link = media_root_path / "media"
    try:
        if not link.exists():
            link.symlink_to(media_root_path)
    except OSError:
        pass  # например, на Windows без прав — картинки в PDF просто не подтянутся
    document = HTML(string=html, base_url=media_root)
    return document.write_pdf()


def export_issue_pdf(issue, save_to_field: bool = True):
    """Формирует PDF и (опционально) сохраняет его в ``issue.pdf_file``.

    Возвращает tuple (pdf_bytes, filename).
    """
    pdf_bytes = build_issue_pdf(issue)
    safe_number = "".join(
        c for c in str(issue.number) if c.isalnum() or c in "-_"
    ) or f"issue-{issue.pk}"
    filename = f"gazeta_{safe_number}_{timezone.localdate():%Y%m%d}.pdf"
    if save_to_field:
        # Имя с меткой времени, чтобы FieldFile.save перезаписывал файл,
        # а не создавал gazeta_..._1.pdf при каждом экспорте.
        issue.pdf_file.delete(save=False)
        issue.pdf_file.save(filename, ContentFile(pdf_bytes), save=True)
    return pdf_bytes, filename
