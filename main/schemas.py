from ninja import ModelSchema, Schema

from courses.schemas import CourseSchema
from materials.schemas import AuthorSchema, VideoSchema

from .models import Post


class PostSchema(ModelSchema):
    """Схема Ninja для поста"""

    class Meta:
        model = Post
        fields = ("id", "title", "content", "post_type", "created_at", "updated_at")


# Сборная схема для главной страницы (паттерн BFF - Backend for Frontend)
class HomeSchema(Schema):
    """Сборная схема для главной страницы (паттерн BFF):
    текущее видео, свежие посты, авторы и активные курсы"""

    current_video: VideoSchema | None = None
    recent_posts: list[PostSchema]
    authors: list[AuthorSchema]
    active_courses: list[CourseSchema]
