from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from accounts.models import Authors
from materials.models import VideoContent, AudioContent, TextContent
from .forms import VideoContentForm, AudioContentForm, TextContentForm


def is_author(user):
    return user.is_authenticated and user.user_type == "author"


@login_required
@user_passes_test(is_author, login_url="admin:login")
def dashboard(request):
    author = Authors.objects.get(user=request.user)
    videos = VideoContent.objects.filter(author=author)
    audios = AudioContent.objects.filter(author=author)
    texts = TextContent.objects.filter(author=author)
    context = {
        "author": author,
        "videos": videos,
        "audios": audios,
        "texts": texts,
    }
    return render(request, "studio/dashboard.html", context)


@login_required
@user_passes_test(is_author)
def video_create(request):
    if request.method == "POST":
        form = VideoContentForm(request.POST, request.FILES)
        if form.is_valid():
            video = form.save(commit=False)
            video.author = Authors.objects.get(user=request.user)
            video.save()
            messages.success(request, "Видео успешно создано.")
            return redirect("studio_dashboard")
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
            return redirect("studio_dashboard")
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
        return redirect("studio_dashboard")
    return render(
        request, "studio/confirm_delete.html", {"object": video, "type": "видео"}
    )


@login_required
@user_passes_test(is_author)
def audio_create(request):
    if request.method == "POST":
        form = AudioContentForm(request.POST, request.FILES)
        if form.is_valid():
            audio = form.save(commit=False)
            audio.author = Authors.objects.get(user=request.user)
            audio.save()
            messages.success(request, "Аудио создано.")
            return redirect("studio_dashboard")
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
            return redirect("studio_dashboard")
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
        return redirect("studio_dashboard")
    return render(
        request, "studio/confirm_delete.html", {"object": audio, "type": "аудио"}
    )


@login_required
@user_passes_test(is_author)
def text_create(request):
    if request.method == "POST":
        form = TextContentForm(request.POST, request.FILES)
        if form.is_valid():
            text = form.save(commit=False)
            text.author = Authors.objects.get(user=request.user)
            text.save()
            messages.success(request, "Статья создана.")
            return redirect("studio_dashboard")
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
            return redirect("studio_dashboard")
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
        return redirect("studio_dashboard")
    return render(
        request, "studio/confirm_delete.html", {"object": text, "type": "текст"}
    )
