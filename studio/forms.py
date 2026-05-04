# studio/forms.py
from django import forms
from courses.models import Course
from materials.models import VideoContent, AudioContent, TextContent


class VideoContentForm(forms.ModelForm):
    class Meta:
        model = VideoContent
        fields = [
            "title",
            "description",
            "embed_code",
            "category",
            "thumbnail",
            "is_live",
            "status",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Название"}
            ),
            "description": forms.Textarea(
                attrs={"class": "form-control", "placeholder": "Описание", "rows": 3}
            ),
            "embed_code": forms.Textarea(
                attrs={"class": "form-control", "placeholder": "Код вставки", "rows": 3}
            ),
            "category": forms.Select(attrs={"class": "form-select"}),
            "thumbnail": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "is_live": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }


class AudioContentForm(forms.ModelForm):
    class Meta:
        model = AudioContent
        fields = [
            "title",
            "description",
            "audio_file",
            "category",
            "cover_image",
            "status",
        ]
        widgets = {
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
    class Meta:
        model = TextContent
        fields = [
            "title",
            "subtitle",
            "content",
            "description",
            "cover_image",
            "category",
            "status",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Название"}
            ),
            "subtitle": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Подзаголовок"}
            ),
            # Вместо textarea теперь скрытое поле – его заполнит редактор
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
    class Meta:
        model = Course
        fields = ["title", "description", "status", "published_at"]
        widgets = {
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
