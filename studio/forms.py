import re

from django import forms
from django.core.exceptions import ValidationError

from courses.models import Course, Lesson
from materials.models import AudioContent, TextContent, VideoContent


class VideoContentForm(forms.ModelForm):
    """Форма создания и редактирования видеоматериала в студии"""

    class Meta:
        model = VideoContent
        fields = (
            "title",
            "description",
            "embed_code",
            "category",
            "thumbnail",
            "is_live",
            "status",
        )
        widgets = {  # noqa: RUF012 - словарь виджетов, стандартный паттерн Django
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Название"}
            ),
            "description": forms.Textarea(
                attrs={"class": "form-control", "placeholder": "Описание", "rows": 3}
            ),
            "embed_code": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Код iframe или ссылка (rutube.ru/video/...)",
                    "rows": 3,
                }
            ),
            "category": forms.Select(attrs={"class": "form-select"}),
            "thumbnail": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "is_live": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # published_at не входит в Meta.fields, добавляем его вручную (необязательным)
        # вместе с виджетом, чтобы использовать в шаблоне для планирования публикации.
        self.fields["published_at"] = forms.DateTimeField(
            required=False,
            label="Дата публикации",
            widget=forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"}
            ),
        )
        instance = self.instance
        if instance is not None and instance.pk and instance.published_at:
            self.initial["published_at"] = instance.published_at.strftime(
                "%Y-%m-%dT%H:%M"
            )

    def save(self, commit=True):
        video = super().save(commit=commit)
        # Сохраняем дату публикации, если она указана в форме
        published_at = self.cleaned_data.get("published_at")
        if published_at is not None:
            VideoContent.objects.filter(pk=video.pk).update(
                published_at=published_at
            )
            video.published_at = published_at
        return video

    def clean_embed_code(self):
        """Проверяет поле embed_code: принимает валидный iframe-код
        или ссылку на видео (например, Rutube), иначе — ошибка валидации."""
        code = self.cleaned_data.get("embed_code", "").strip()
        if not code:
            raise ValidationError("Необходимо вставить код или ссылку на видео.")

        if "<iframe" in code:
            if not re.search(
                r'<\s*iframe\s[^>]*src\s*=\s*["\']https?://', code, re.IGNORECASE
            ):
                raise ValidationError("Неверный формат iframe.")
            return code

        if self._is_valid_video_url(code):
            return code

        raise ValidationError(
            "Введите корректный iframe-код или ссылку на видео (например, rutube.ru/video/...)"
        )

    @staticmethod
    def _is_valid_video_url(url):
        """Проверяет, является ли строка корректной ссылкой на видео Rutube."""
        return bool(re.search(r"rutube\.ru/video/[a-f0-9]+", url))


class AudioContentForm(forms.ModelForm):
    """Форма создания и редактирования аудиоматериала в студии"""

    class Meta:
        model = AudioContent
        fields = (
            "title",
            "description",
            "audio_file",
            "category",
            "cover_image",
            "status",
        )
        widgets = {  # noqa: RUF012 - словарь виджетов, стандартный паттерн Django
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Название"}
            ),
            "description": forms.Textarea(
                attrs={"class": "form-control", "placeholder": "Описание", "rows": 3}
            ),
            "audio_file": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "cover_image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }


class TextContentForm(forms.ModelForm):
    """Форма создания и редактирования текстового материала в студии"""

    class Meta:
        model = TextContent
        fields = (
            "title",
            "subtitle",
            "content",
            "description",
            "cover_image",
            "category",
            "status",
        )
        widgets = {  # noqa: RUF012 - словарь виджетов, стандартный паттерн Django
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Название"}
            ),
            "subtitle": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Подзаголовок"}
            ),
            "content": forms.HiddenInput(),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Краткое описание",
                    "rows": 3,
                }
            ),
            "category": forms.Select(attrs={"class": "form-select"}),
            "cover_image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }


class CourseForm(forms.ModelForm):
    """Форма создания и редактирования курса в студии"""

    class Meta:
        model = Course
        fields = ("title", "description", "status", "published_at")
        widgets = {  # noqa: RUF012 - словарь виджетов, стандартный паттерн Django
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Название курса"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Описание курса",
                }
            ),
            "status": forms.Select(attrs={"class": "form-select"}),
            "published_at": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"}
            ),
        }


class LessonForm(forms.ModelForm):
    """Форма создания и редактирования урока в студии"""

    class Meta:
        model = Lesson
        fields = ("title", "description", "order", "video", "audio", "text")
        widgets = {  # noqa: RUF012 - словарь виджетов, стандартный паттерн Django
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Название урока"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Краткое описание",
                }
            ),
            "order": forms.HiddenInput(),
            "video": forms.HiddenInput(),
            "audio": forms.HiddenInput(),
            "text": forms.HiddenInput(),
        }
