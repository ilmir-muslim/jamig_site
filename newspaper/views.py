from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import NewspaperBlockForm, NewspaperIssueForm
from .models import NewspaperBlock, NewspaperIssue


def is_newspaper_editor(user):
    """Проверка доступа: True, если пользователь — редактор газеты (или суперuser)."""
    return user.is_authenticated and (
        user.user_type == "newspaper_editor" or user.is_superuser
    )


# ---------- ПУБЛИЧНАЯ ЧАСТЬ ----------


def issue_list(request):
    """Архив выпусков газеты (электронная версия)."""
    issues = (
        NewspaperIssue.objects.filter(status="published")
        .prefetch_related("blocks")
    )
    return render(request, "newspaper/issue_list.html", {"issues": issues})


def issue_detail(request, slug):
    """Страница выпуска газеты: классическая газетная вёрстка из блоков."""
    issue = get_object_or_404(NewspaperIssue, slug=slug, status="published")
    issue.views_count += 1
    issue.save(update_fields=["views_count"])
    # related_name="blocks" обратная связь ForeignKey — Pylance не видит её статически
    blocks = issue.blocks.all().order_by("order", "id")  # type: ignore[attr-defined]
    previous = (
        NewspaperIssue.objects.filter(
            status="published", issue_date__lt=issue.issue_date
        )
        .order_by("-issue_date")
        .first()
    )
    newer = (
        NewspaperIssue.objects.filter(
            status="published", issue_date__gt=issue.issue_date
        )
        .order_by("issue_date")
        .first()
    )
    context = {
        "issue": issue,
        "blocks": blocks,
        "previous_issue": previous,
        "next_issue": newer,
    }
    return render(request, "newspaper/issue_detail.html", context)


# ---------- КОНСТРУКТОР (РЕДАКТОР ГАЗЕТЫ) ----------


@login_required
@user_passes_test(is_newspaper_editor, login_url="login")
def editor_dashboard(request):
    """Конструктор газеты: список выпусков редактора."""
    issues = NewspaperIssue.objects.select_related("editor").order_by("-issue_date")
    if not request.user.is_superuser:
        issues = issues.filter(editor=request.user)
    return render(
        request, "newspaper/editor_dashboard.html", {"issues": issues}
    )


@login_required
@user_passes_test(is_newspaper_editor, login_url="login")
def issue_create(request):
    """Создание нового выпуска газеты."""
    if request.method == "POST":
        form = NewspaperIssueForm(request.POST, request.FILES)
        if form.is_valid():
            issue = form.save(commit=False)
            issue.editor = request.user
            issue.save()
            messages.success(request, f"Выпуск «{issue.title}» создан. Добавьте материалы.")
            return redirect("newspaper_editor_issue_edit", pk=issue.pk)
    else:
        form = NewspaperIssueForm()
    return render(
        request,
        "newspaper/issue_form.html",
        {"form": form, "action": "create", "issue": None},
    )


@login_required
@user_passes_test(is_newspaper_editor, login_url="login")
def issue_edit(request, pk):
    """Конструктор выпуска: параметры номера + полосная вёрстка из материалов."""
    issue = _get_editor_issue(request, pk)
    block_form = NewspaperBlockForm()
    if request.method == "POST":
        form = NewspaperIssueForm(request.POST, request.FILES, instance=issue)
        if form.is_valid():
            form.save()
            messages.success(request, "Выпуск обновлён.")
            return redirect("newspaper_editor_issue_edit", pk=issue.pk)
    else:
        form = NewspaperIssueForm(instance=issue)
    blocks_list = list(issue.blocks.all().order_by("order", "id"))  # type: ignore[attr-defined]
    preview_data = [
        {
            "pk": b.pk,
            "title": b.title,
            "subtitle": b.subtitle,
            "type": b.get_block_type_display(),
            "size": b.size,
            "author": b.author_name,
            "html": b.get_content_html(),
            "photo": b.photo.url if b.photo else None,
            "photo_caption": b.photo_caption,
            "gallery": b.get_gallery_images(),
            "is_front_page": b.is_front_page,
        }
        for b in blocks_list
    ]
    return render(
        request,
        "newspaper/issue_form.html",
        {
            "form": form,
            "action": "edit",
            "issue": issue,
            "block_form": block_form,
            "blocks": blocks_list,
            "blocks_json": preview_data,
            "announce_preview": {
                "headline": issue.announce_headline,
                "text": issue.announce_text,
                "image": (
                    issue.announce_image.url if issue.announce_image else None
                ),
                "auto": not bool(issue.description),
            },
        },
    )


@login_required
@user_passes_test(is_newspaper_editor, login_url="login")
def issue_delete(request, pk):
    """Удаление выпуска газеты."""
    issue = _get_editor_issue(request, pk)
    if request.method == "POST":
        issue.delete()
        messages.success(request, "Выпуск удалён.")
        return redirect("newspaper_editor_dashboard")
    return render(
        request, "studio/confirm_delete.html", {"object": issue, "type": "выпуск газеты"}
    )


@login_required
@user_passes_test(is_newspaper_editor, login_url="login")
def block_create(request, issue_pk):
    """Добавление материала в выпуск: заголовки, текст с разметкой, фото, галерея."""
    issue = _get_editor_issue(request, issue_pk)
    if request.method == "POST":
        form = NewspaperBlockForm(request.POST, request.FILES)
        if form.is_valid():
            block = form.save(commit=False)
            block.issue = issue
            # порядок рассчитывается в модели NewspaperBlock.save(), поле order скрыто
            block.order = 0
            block.save()
            _save_gallery_files(block, form.get_all_extra_photos())
            messages.success(request, f"Материал «{block.title}» добавлён в выпуск.")
        else:
            messages.error(request, "Исправьте ошибки в форме материала.")
    return redirect("newspaper_editor_issue_edit", pk=issue.pk)


@login_required
@user_passes_test(is_newspaper_editor, login_url="login")
def block_edit(request, pk):
    """Редактирование материала выпуска (полноценный редактор статьи)."""
    block = _get_editor_block(request, pk)
    if request.method == "POST":
        form = NewspaperBlockForm(request.POST, request.FILES, instance=block)
        if form.is_valid():
            updated = form.save()
            _save_gallery_files(updated, form.get_all_extra_photos())
            messages.success(request, "Материал обновлён.")
            return redirect("newspaper_editor_issue_edit", pk=updated.issue.pk)
        messages.error(request, "Исправьте ошибки в форме.")
    gallery_items = []
    for item in block.get_gallery_images():
        gallery_items.append({**item, "path": item["url"].removeprefix("/media/")})
    return render(
        request,
        "newspaper/block_form.html",
        {
            "form": form,
            "block": block,
            "issue": block.issue,
            "action": "edit",
            "gallery_items": gallery_items,
        },
    )


@login_required
@user_passes_test(is_newspaper_editor, login_url="login")
def block_duplicate(request, pk):
    """Дублирование материала — удобно для быстрой сборки похожих полос."""
    block = _get_editor_block(request, pk)
    issue_pk = block.issue.pk
    new_block = NewspaperBlock.objects.get(pk=block.pk)
    new_block.pk = None
    new_block.title = f"{block.title} (копия)"
    new_block.order = 0
    new_block.gallery = list(block.gallery or [])
    new_block.save()
    messages.success(request, "Копия материала создана — отредактируйте её.")
    return redirect("newspaper_editor_block_edit", pk=new_block.pk)


@login_required
@user_passes_test(is_newspaper_editor, login_url="login")
def block_delete(request, pk):
    """Удаление блока выпуска."""
    block = _get_editor_block(request, pk)
    issue_pk = block.issue.pk
    if request.method == "POST":
        block.delete()
        messages.success(request, "Материал удалён.")
    return redirect("newspaper_editor_issue_edit", pk=issue_pk)


@login_required
@require_POST
@user_passes_test(is_newspaper_editor, login_url="login")
def gallery_add(request, pk):
    """AJAX: загрузка фотографии в галерею материала (для конструктора)."""
    block = _get_editor_block(request, pk)
    file = request.FILES.get("image")
    caption = (request.POST.get("caption") or "").strip()
    if not file:
        return JsonResponse({"ok": False, "error": "Файл не получен."}, status=400)
    content_type = getattr(file, "content_type", "") or ""
    if not content_type.startswith("image/"):
        return JsonResponse(
            {"ok": False, "error": "Можно загружать только изображения."}, status=400
        )
    items = list(block.gallery or [])
    saved = _save_image_to_storage(file, block.issue.slug)
    items.append({"image": saved, "caption": caption})
    block.gallery = items
    block.save(update_fields=["gallery"])
    return JsonResponse({"ok": True, "image": saved, "url": f"/media/{saved}", "caption": caption})


@login_required
@require_POST
@user_passes_test(is_newspaper_editor, login_url="login")
def gallery_remove(request, pk):
    """AJAX: удаление фотографии из галереи материала по пути."""
    block = _get_editor_block(request, pk)
    path = request.POST.get("image") or ""
    items = [i for i in (block.gallery or []) if isinstance(i, dict) and i.get("image") != path]
    block.gallery = items
    block.save(update_fields=["gallery"])
    try:
        from django.core.files.storage import default_storage

        if path and default_storage.exists(path):
            default_storage.delete(path)
    except (FileNotFoundError, OSError, ValueError):
        pass
    return JsonResponse({"ok": True})


@login_required
@user_passes_test(is_newspaper_editor, login_url="login")
def block_move(request, pk, direction):
    """Перемещение блока вверх/вниз по порядку полос."""
    block = _get_editor_block(request, pk)
    issue_pk = block.issue.pk
    if direction == "up":
        neighbour = (
            NewspaperBlock.objects.filter(issue=block.issue, order__lt=block.order)
            .order_by("-order")
            .first()
        )
    elif direction == "down":
        neighbour = (
            NewspaperBlock.objects.filter(issue=block.issue, order__gt=block.order)
            .order_by("order")
            .first()
        )
    else:
        neighbour = None
    if neighbour:
        block.order, neighbour.order = neighbour.order, block.order
        block.save(update_fields=["order"])
        neighbour.save(update_fields=["order"])
    return redirect("newspaper_editor_issue_edit", pk=issue_pk)


# ---------- ВСПОМОГАТЕЛЬНЫЕ ----------


def _save_image_to_storage(file, slug):
    """Сохраняет загруженное изображение в MEDIA_ROOT и возвращает относительный путь."""
    import os
    import uuid

    from django.conf import settings

    ext = os.path.splitext(getattr(file, "name", ""))[1].lower() or ".jpg"
    if ext not in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
        ext = ".jpg"
    subdir = f"newspaper/gallery/{slug or 'tmp'}"
    name = f"{uuid.uuid4().hex[:12]}{ext}"
    rel_path = os.path.join(subdir, name)
    full_path = os.path.join(settings.MEDIA_ROOT, subdir)
    os.makedirs(full_path, exist_ok=True)
    with open(os.path.join(settings.MEDIA_ROOT, rel_path), "wb") as dest:
        for chunk in file.chunks():
            dest.write(chunk)
    return rel_path.replace("\\", "/")


def _save_gallery_files(block, files):
    """Добавляет несколько загруженных фото в JSON-галерею материала."""
    if not files:
        return
    items = list(block.gallery or [])
    for f in files:
        path = _save_image_to_storage(f, block.issue.slug)
        items.append({"image": path, "caption": ""})
    block.gallery = items
    block.save(update_fields=["gallery"])


def _get_editor_issue(request, pk):
    """Возвращает выпуск, доступный текущему редактору (или любой — для суперадмина)."""
    qs = NewspaperIssue.objects.all()
    if not request.user.is_superuser:
        qs = qs.filter(editor=request.user)
    return get_object_or_404(qs, pk=pk)


def _get_editor_block(request, pk):
    """Возвращает блок выпуска, доступного текущему редактору."""
    block = get_object_or_404(NewspaperBlock, pk=pk)
    _get_editor_issue(request, block.issue.pk)
    return block
