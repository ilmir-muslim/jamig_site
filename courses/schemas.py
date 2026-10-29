from typing import ClassVar

from django.db.models import QuerySet
from ninja import Field, ModelSchema

from materials.schemas import AudioSchema, AuthorSchema, TextSchema, VideoSchema

from .models import Course, Lesson


class CourseSchema(ModelSchema):
    """Схема Ninja для курса с вложенной информацией об авторе"""

    author: AuthorSchema | None = None

    class Meta:
        model = Course
        fields: ClassVar[list[str]] = [
            "id",
            "title",
            "slug",
            "description",
            "status",
            "published_at",
        ]


class LessonSchema(ModelSchema):
    """Схема Ninja для урока с вложенными схемами материалов"""

    # Подтягиваем детальные схемы материалов из соседнего приложения
    video: VideoSchema | None = None
    audio: AudioSchema | None = None
    text: TextSchema | None = None

    class Meta:
        model = Lesson
        fields: ClassVar[list[str]] = ["id", "title", "description", "order"]


class CourseDetailSchema(CourseSchema):
    """Детальная схема курса: дополняет CourseSchema списком уроков"""

    # При запросе детального курса отдаем и список его уроков
    lessons: list[LessonSchema] = Field(default_factory=list)

    @staticmethod
    def resolve_lessons(obj: Course) -> QuerySet[Lesson]:
        """Резолвер Ninja: возвращает все уроки курса для детальной схемы."""
        return obj.lessons.all()  # type: ignore[attr-defined]
