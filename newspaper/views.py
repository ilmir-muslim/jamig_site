from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

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
    issues = NewspaperIssue.objects.filter(status="published")
    return render(request, "newspaper/issue_list.html", {"issues": issues})


def issue_detail(request, slug):
    """Страница выпуска газеты: классическая газетная вёрстка из блоков."""
    issue = get_object_or_404(NewspaperIssue, slug=slug, status="published")
    issue.views_count += 1
    issue.save(update_fields=["views_count"])
    blocks = issue.blocks.all()
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
    """Редактирование выпуска и конструктор его полос (блоков)."""
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
    return render(
        request,
        "newspaper/issue_form.html",
        {
            "form": form,
            "action": "edit",
            "issue": issue,
            "block_form": block_form,
            "blocks": issue.blocks.all(),
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
    """Добавление блока (полосы) в выпуск: текст, фото, тип материала."""
    issue = _get_editor_issue(request, issue_pk)
    if request.method == "POST":
        form = NewspaperBlockForm(request.POST, request.FILES)
        if form.is_valid():
            block = form.save(commit=False)
            block.issue = issue
            form.fields.pop("order", None)
            block.save()
            messages.success(request, "Материал добавлён в выпуск.")
        else:
            messages.error(request, "Исправьте ошибки в форме материала.")
    return redirect("newspaper_editor_issue_edit", pk=issue.pk)


@login_required
@user_passes_test(is_newspaper_editor, login_url="login")
def block_edit(request, pk):
    """Редактирование блока выпуска."""
    block = _get_editor_block(request, pk)
    if request.method == "POST":
        form = NewspaperBlockForm(request.POST, request.FILES, instance=block)
        if form.is_valid():
            form.save()
            messages.success(request, "Материал обновлён.")
            return redirect("newspaper_editor_issue_edit", pk=block.issue.pk)
    else:
        form = NewspaperBlockForm(instance=block)
    return render(
        request,
        "newspaper/block_form.html",
        {"form": form, "block": block, "issue": block.issue, "action": "edit"},
    )


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
