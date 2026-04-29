from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Sum
from accounts.models import Authors
from materials.models import VideoContent, AudioContent, TextContent
from .forms import VideoContentForm, AudioContentForm, TextContentForm


def is_author(user):
    return user.is_authenticated and user.user_type == "author"


@login_required
@user_passes_test(is_author, login_url="admin:login")
def dashboard(request):
    author = Authors.objects.get(user=request.user)
    # Статистика
    total_videos = VideoContent.objects.filter(author=author).count()
    published_videos = VideoContent.objects.filter(
        author=author, status="published"
    ).count()
    total_audios = AudioContent.objects.filter(author=author).count()
    published_audios = AudioContent.objects.filter(
        author=author, status="published"
    ).count()
    total_texts = TextContent.objects.filter(author=author).count()
    published_texts = TextContent.objects.filter(
        author=author, status="published"
    ).count()

    # Общее количество просмотров (сумма по всем материалам)
    video_views = (
        VideoContent.objects.filter(author=author).aggregate(s=Sum("views_count"))["s"]
        or 0
    )
    audio_views = (
        AudioContent.objects.filter(author=author).aggregate(s=Sum("views_count"))["s"]
        or 0
    )
    text_views = (
        TextContent.objects.filter(author=author).aggregate(s=Sum("views_count"))["s"]
        or 0
    )
    total_views = video_views + audio_views + text_views

    stats = {
        "total_videos": total_videos,
        "published_videos": published_videos,
        "total_audios": total_audios,
        "published_audios": published_audios,
        "total_texts": total_texts,
        "published_texts": published_texts,
        "total_views": total_views,
    }

    recent_videos = VideoContent.objects.filter(author=author).order_by("-updated_at")[
        :5
    ]
    recent_texts = TextContent.objects.filter(author=author).order_by("-updated_at")[:5]

    context = {
        "stats": stats,
        "recent_videos": recent_videos,
        "recent_texts": recent_texts,
    }
    return render(request, "studio/dashboard.html", context)


def _get_author(request):
    return Authors.objects.get(user=request.user)


def _status_filter(request, queryset, status_param="status"):
    status = request.GET.get(status_param, "all")
    if status in ["draft", "published", "archived"]:
        queryset = queryset.filter(status=status)
    return queryset, status


# ---------- ВИДЕО ----------
@login_required
@user_passes_test(is_author)
def video_list(request):
    author = _get_author(request)
    qs = VideoContent.objects.filter(author=author).order_by("-updated_at")
    qs, current_filter = _status_filter(request, qs)
    context = {
        "videos": qs,
        "current_filter": current_filter,
    }
    return render(request, "studio/video_list.html", context)


@login_required
@user_passes_test(is_author)
def video_create(request):
    if request.method == "POST":
        form = VideoContentForm(request.POST, request.FILES)
        if form.is_valid():
            video = form.save(commit=False)
            video.author = _get_author(request)
            video.save()
            messages.success(request, "Видео успешно создано.")
            return redirect("studio_video_list")
    else:
        form = VideoContentForm()
    return render(request, "studio/video_form.html", {"form": form, "action": "create"})


@login_required
@user_passes_test(is_author)
def video_edit(request, pk):
    video = get_object_or_404(VideoContent, pk=pk, author__user=request.user)
    if request.method == "POST":
        form = VideoContentForm(request.POST, request.FILES, instance=video)
        if form.is_valid():
            form.save()
            messages.success(request, "Видео обновлено.")
            return redirect("studio_video_list")
    else:
        form = VideoContentForm(instance=video)
    return render(request, "studio/video_form.html", {"form": form, "action": "edit"})


@login_required
@user_passes_test(is_author)
def video_delete(request, pk):
    video = get_object_or_404(VideoContent, pk=pk, author__user=request.user)
    if request.method == "POST":
        video.delete()
        messages.success(request, "Видео удалено.")
        return redirect("studio_video_list")
    return render(
        request, "studio/confirm_delete.html", {"object": video, "type": "видео"}
    )


# ---------- АУДИО ----------
@login_required
@user_passes_test(is_author)
def audio_list(request):
    author = _get_author(request)
    qs = AudioContent.objects.filter(author=author).order_by("-updated_at")
    qs, current_filter = _status_filter(request, qs)
    context = {
        "audios": qs,
        "current_filter": current_filter,
    }
    return render(request, "studio/audio_list.html", context)


@login_required
@user_passes_test(is_author)
def audio_create(request):
    if request.method == "POST":
        form = AudioContentForm(request.POST, request.FILES)
        if form.is_valid():
            audio = form.save(commit=False)
            audio.author = _get_author(request)
            audio.save()
            messages.success(request, "Аудио создано.")
            return redirect("studio_audio_list")
    else:
        form = AudioContentForm()
    return render(request, "studio/audio_form.html", {"form": form, "action": "create"})


@login_required
@user_passes_test(is_author)
def audio_edit(request, pk):
    audio = get_object_or_404(AudioContent, pk=pk, author__user=request.user)
    if request.method == "POST":
        form = AudioContentForm(request.POST, request.FILES, instance=audio)
        if form.is_valid():
            form.save()
            messages.success(request, "Аудио обновлено.")
            return redirect("studio_audio_list")
    else:
        form = AudioContentForm(instance=audio)
    return render(request, "studio/audio_form.html", {"form": form, "action": "edit"})


@login_required
@user_passes_test(is_author)
def audio_delete(request, pk):
    audio = get_object_or_404(AudioContent, pk=pk, author__user=request.user)
    if request.method == "POST":
        audio.delete()
        messages.success(request, "Аудио удалено.")
        return redirect("studio_audio_list")
    return render(
        request, "studio/confirm_delete.html", {"object": audio, "type": "аудио"}
    )


# ---------- СТАТЬИ ----------
@login_required
@user_passes_test(is_author)
def text_list(request):
    author = _get_author(request)
    qs = TextContent.objects.filter(author=author).order_by("-updated_at")
    qs, current_filter = _status_filter(request, qs)
    context = {
        "texts": qs,
        "current_filter": current_filter,
    }
    return render(request, "studio/text_list.html", context)


@login_required
@user_passes_test(is_author)
def text_create(request):
    if request.method == "POST":
        form = TextContentForm(request.POST, request.FILES)
        if form.is_valid():
            text = form.save(commit=False)
            text.author = _get_author(request)
            text.save()
            messages.success(request, "Статья создана.")
            return redirect("studio_text_list")
    else:
        form = TextContentForm()
    return render(request, "studio/text_form.html", {"form": form, "action": "create"})


@login_required
@user_passes_test(is_author)
def text_edit(request, pk):
    text = get_object_or_404(TextContent, pk=pk, author__user=request.user)
    if request.method == "POST":
        form = TextContentForm(request.POST, request.FILES, instance=text)
        if form.is_valid():
            form.save()
            messages.success(request, "Статья обновлена.")
            return redirect("studio_text_list")
    else:
        form = TextContentForm(instance=text)
    return render(request, "studio/text_form.html", {"form": form, "action": "edit"})


@login_required
@user_passes_test(is_author)
def text_delete(request, pk):
    text = get_object_or_404(TextContent, pk=pk, author__user=request.user)
    if request.method == "POST":
        text.delete()
        messages.success(request, "Статья удалена.")
        return redirect("studio_text_list")
    return render(
        request, "studio/confirm_delete.html", {"object": text, "type": "текст"}
    )
