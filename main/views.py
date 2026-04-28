from django.shortcuts import render, get_object_or_404
from .models import Post
from materials.models import VideoContent, AudioContent, TextContent
from accounts.models import Authors


def home(request):
    # Последнее опубликованное видео
    try:
        current_video = (
            VideoContent.objects.filter(status="published")
            .select_related("author", "category")
            .latest("published_at")
        )
    except VideoContent.DoesNotExist:
        current_video = None

    # Последние новости
    recent_posts = Post.objects.filter(is_published=True)[:5]

    # Популярные авторы (первые 4)
    authors = Authors.objects.filter(show_in_authors_list=True)[:4]

    # Активные курсы (последние 3)
    from courses.models import Course

    active_courses = Course.objects.filter(status="published")[:3]

    context = {
        "current_video": current_video,
        "recent_posts": recent_posts,
        "authors": authors,
        "active_courses": active_courses,
    }

    return render(request, "main/home.html", context)


def author_list(request):
    """Список всех авторов"""
    authors = Authors.objects.filter(show_in_authors_list=True)
    return render(request, "main/author_list.html", {"authors": authors})


def author_detail(request, pk):
    """Страница конкретного автора с его материалами"""
    author = get_object_or_404(Authors, pk=pk)
    videos = VideoContent.objects.filter(author=author, status="published")
    audios = AudioContent.objects.filter(author=author, status="published")
    texts = TextContent.objects.filter(author=author, status="published")

    context = {
        "author": author,
        "videos": videos,
        "audios": audios,
        "texts": texts,
    }
    return render(request, "main/author_detail.html", context)
