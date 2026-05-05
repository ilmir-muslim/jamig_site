import json
import time

from django.db import transaction, OperationalError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView, DetailView
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from .models import VideoContent, AudioContent, TextContent, Category, ReadingProgress


class VideoListView(ListView):
    model = VideoContent
    template_name = "materials/video_list.html"
    context_object_name = "videos"
    paginate_by = 12

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .filter(status="published")
            .select_related("author", "category")
        )
        category = self.request.GET.get("category")
        author = self.request.GET.get("author")
        if category:
            qs = qs.filter(category__slug=category)
        if author:
            qs = qs.filter(author__user__username=author)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.filter(is_active=True)
        return context


class VideoDetailView(DetailView):
    model = VideoContent
    template_name = "materials/video_detail.html"
    context_object_name = "video"


class AudioListView(ListView):
    model = AudioContent
    template_name = "materials/audio_list.html"
    context_object_name = "audios"
    paginate_by = 12

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .filter(status="published")
            .select_related("author", "category")
        )
        category = self.request.GET.get("category")
        author = self.request.GET.get("author")
        if category:
            qs = qs.filter(category__slug=category)
        if author:
            qs = qs.filter(author__user__username=author)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.filter(is_active=True)
        return context


class AudioDetailView(DetailView):
    model = AudioContent
    template_name = "materials/audio_detail.html"
    context_object_name = "audio"


class TextListView(ListView):
    model = TextContent
    template_name = "materials/text_list.html"
    context_object_name = "texts"
    paginate_by = 12

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .filter(status="published")
            .select_related("author", "category")
        )
        category = self.request.GET.get("category")
        author = self.request.GET.get("author")
        if category:
            qs = qs.filter(category__slug=category)
        if author:
            qs = qs.filter(author__user__username=author)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.filter(is_active=True)
        return context


# ================== ЧИТАЛКА ==================
def reader_view(request, slug):
    text = get_object_or_404(TextContent, slug=slug, status="published")
    chapter_content = text.content
    server_page = None
    if request.user.is_authenticated:
        progress = ReadingProgress.objects.filter(user=request.user, text=text).first()
        if progress:
            server_page = progress.page_number
    context = {
        "text": text,
        "chapter_content": chapter_content,
        "server_page": server_page,
        "text_id": text.id,
    }
    return render(request, "materials/reader.html", context)


@login_required
@require_POST
def save_progress(request):
    data = json.loads(request.body)
    text_id = data.get("text_id")
    page_number = data.get("page_number", 1)
    text = get_object_or_404(TextContent, pk=text_id)

    max_retries = 3
    for attempt in range(max_retries):
        try:
            with transaction.atomic():
                ReadingProgress.objects.update_or_create(
                    user=request.user,
                    text=text,
                    defaults={"page_number": page_number},
                )
            break 
        except OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                time.sleep(0.3 * (attempt + 1)) 
            else:
                raise  

    return JsonResponse({"status": "ok"})
