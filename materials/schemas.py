from ninja import ModelSchema, Schema
from typing import Optional
from datetime import datetime
from .models import Category, VideoContent, AudioContent, TextContent
from accounts.models import Authors


class CategorySchema(ModelSchema):
    class Meta:
        model = Category
        fields = ["id", "title", "slug", "description"]


class AuthorSchema(ModelSchema):
    full_name: str

    @staticmethod
    def resolve_full_name(obj):
        return obj.user.get_full_name()

    class Meta:
        model = Authors
        fields = ["id", "specialization"]


class VideoSchema(ModelSchema):
    category: Optional[CategorySchema] = None
    author: Optional[AuthorSchema] = None

    class Meta:
        model = VideoContent
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "views_count",
            "published_at",
            "embed_code",
            "duration",
            "thumbnail",
            "is_live",
        ]


class AudioSchema(ModelSchema):
    category: Optional[CategorySchema] = None
    author: Optional[AuthorSchema] = None

    class Meta:
        model = AudioContent
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "views_count",
            "published_at",
            "audio_file",
            "duration",
            "cover_image",
            "listens_count",
        ]


class TextSchema(ModelSchema):
    category: Optional[CategorySchema] = None
    author: Optional[AuthorSchema] = None

    class Meta:
        model = TextContent
        fields = [
            "id",
            "title",
            "slug",
            "subtitle",
            "description",
            "views_count",
            "published_at",
            "content",
            "cover_image",
            "reading_time",
        ]
