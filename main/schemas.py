from ninja import ModelSchema, Schema
from typing import List, Optional
from .models import Post
from materials.schemas import VideoSchema, AuthorSchema
from courses.schemas import CourseSchema


class PostSchema(ModelSchema):
    class Meta:
        model = Post
        fields = ["id", "title", "content", "post_type", "created_at", "updated_at"]


# Сборная схема для главной страницы (паттерн BFF - Backend for Frontend)
class HomeSchema(Schema):
    current_video: Optional[VideoSchema] = None
    recent_posts: List[PostSchema]
    authors: List[AuthorSchema]
    active_courses: List[CourseSchema]
