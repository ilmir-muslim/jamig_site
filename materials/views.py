from django.views.generic import ListView, DetailView
from .models import VideoContent, AudioContent, TextContent, Category
from django.db.models import Q


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
            qs = qs.filter(author__user__username=author)  # или author__id
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


class TextDetailView(DetailView):
    model = TextContent
    template_name = "materials/text_detail.html"
    context_object_name = "text"
