from ninja import ModelSchema
from typing import List, Optional
from .models import Course, Lesson
from materials.schemas import AuthorSchema, VideoSchema, AudioSchema, TextSchema


class CourseSchema(ModelSchema):
    author: Optional[AuthorSchema] = None

    class Meta:
        model = Course
        fields = ["id", "title", "slug", "description", "status", "published_at"]


class LessonSchema(ModelSchema):
    # Подтягиваем детальные схемы материалов из соседнего приложения
    video: Optional[VideoSchema] = None
    audio: Optional[AudioSchema] = None
    text: Optional[TextSchema] = None

    class Meta:
        model = Lesson
        fields = ["id", "title", "description", "order"]


class CourseDetailSchema(CourseSchema):
    # При запросе детального курса отдаем и список его уроков
    lessons: List[LessonSchema] = []

    @staticmethod
    def resolve_lessons(obj):
        return obj.lessons.all()
