from ninja import ModelSchema

from accounts.models import Authors

from .models import AudioContent, Category, TextContent, VideoContent


class CategorySchema(ModelSchema):
    """Схема Ninja для категории"""

    class Meta:
        model = Category
        fields = ("id", "title", "slug", "description")


class AuthorSchema(ModelSchema):
    """Схема Ninja для автора: добавляет полное имя из связанного пользователя"""

    full_name: str

    @staticmethod
    def resolve_full_name(obj):
        """Резолвер Ninja: полное имя автора из связанного пользователя."""
        return obj.user.get_full_name()

    class Meta:
        model = Authors
        fields = ("id", "specialization")


class VideoSchema(ModelSchema):
    """Схема Ninja для видеоматериала с категорией и автором"""

    category: CategorySchema | None = None
    author: AuthorSchema | None = None

    class Meta:
        model = VideoContent
        fields = (
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
        )


class AudioSchema(ModelSchema):
    """Схема Ninja для аудиоматериала с категорией и автором"""

    category: CategorySchema | None = None
    author: AuthorSchema | None = None

    class Meta:
        model = AudioContent
        fields = (
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
        )


class TextSchema(ModelSchema):
    """Схема Ninja для текстовой статьи с категорией и автором"""

    category: CategorySchema | None = None
    author: AuthorSchema | None = None

    class Meta:
        model = TextContent
        fields = (
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
        )
