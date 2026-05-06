import io
import re
import json
import time

from weasyprint import HTML

from django.db import transaction, OperationalError
from django.http import JsonResponse, HttpResponse, Http404
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
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


def download_text(request, slug, format):
    text = get_object_or_404(TextContent, slug=slug, status="published")

    # Безопасное имя файла из заголовка
    from django.utils.text import slugify as django_slugify

    safe_filename = django_slugify(text.title) or text.slug

    if format == "txt":
        clean = re.sub(r"<[^>]+>", "", text.content)
        response = HttpResponse(clean, content_type="text/plain; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{safe_filename}.txt"'
        return response

    elif format == "pdf":
        html_str = render_to_string("materials/reader_pdf.html", {"text": text})
        pdf_file = io.BytesIO()
        HTML(string=html_str, base_url=request.build_absolute_uri("/")).write_pdf(
            pdf_file
        )
        pdf_file.seek(0)
        response = HttpResponse(pdf_file.read(), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{safe_filename}.pdf"'
        return response

    elif format == "epub":
        try:
            from ebooklib import epub
        except ImportError:
            raise Http404("EPUB generation is not available. Install ebooklib.")

        book = epub.EpubBook()
        book.set_identifier(f"text-{text.id}")
        book.set_title(text.title)
        book.set_language("ru")
        book.add_author(text.author.user.get_full_name() if text.author else "Unknown")

        chapter = epub.EpubHtml(title=text.title, file_name="content.xhtml", lang="ru")
        chapter.content = f"<h1>{text.title}</h1>{text.content}"
        book.add_item(chapter)

        book.toc = (epub.Link("content.xhtml", text.title, "content"),)
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        book.spine = ["nav", chapter]

        epub_data = io.BytesIO()
        epub.write_epub(epub_data, book)
        epub_data.seek(0)

        response = HttpResponse(epub_data.read(), content_type="application/epub+zip")
        response["Content-Disposition"] = f'attachment; filename="{safe_filename}.epub"'
        return response

    else:
        raise Http404("Unsupported format")


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    videos = VideoContent.objects.filter(category=category, status="published")
    audios = AudioContent.objects.filter(category=category, status="published")
    texts = TextContent.objects.filter(category=category, status="published")
    context = {
        "category": category,
        "videos": videos,
        "audios": audios,
        "texts": texts,
    }
    return render(request, "materials/category_detail.html", context)
