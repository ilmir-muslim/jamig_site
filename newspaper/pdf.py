"""Экспорт выпуска газеты в PDF (печатная версия для типографии).

Генерация выполняется через WeasyPrint из отдельного печатного шаблона
``templates/newspaper/issue_print.html``: формат A3 альбомный — классическая
складная газета, колонки, засечные шрифты, обрыв текста по колонкам.

Шрифт Tahoma задан как основной, но WeasyPrint использует его только если
шрифт установлен в системе (Windows). На Linux он автоматически заменится
на доступный serif-шрифт (DejaVu Serif и т.п.), поэтому верстка не сломается.
"""

from django.conf import settings
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.utils import timezone


def build_issue_pdf(issue) -> bytes:
    """Рендерит выпуск газеты в PDF и возвращает байты документа."""
    from weasyprint import HTML  # импорт здесь: модуль опционален для окружения

    blocks = list(issue.blocks.all().order_by("order", "id"))
    html = render_to_string(
        "newspaper/issue_print.html",
        {
            "issue": issue,
            "blocks": blocks,
            "generated_at": timezone.localtime(),
        },
    )
    # base_url — MEDIA_ROOT: относительные пути /media/... резолвятся в файлы,
    # а /static/... — через StaticFilesResolver ниже (Django finders).
    document = HTML(string=html, base_url=str(settings.MEDIA_ROOT))
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
