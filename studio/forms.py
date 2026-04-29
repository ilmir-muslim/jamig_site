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
            "duration",
            "thumbnail",
            "is_live",
            "category",
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
            "duration": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "Длительность"}
            ),
            "category": forms.Select(attrs={"class": "form-select"}),
            "thumbnail": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "is_live": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class AudioContentForm(forms.ModelForm):
    class Meta:
        model = AudioContent
        fields = [
            "title",
            "description",
            "audio_file",
            "duration",
            "cover_image",
            "category",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Название"}
            ),
            "description": forms.Textarea(
                attrs={"class": "form-control", "placeholder": "Описание", "rows": 3}
            ),
            "audio_file": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "duration": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "Длительность"}
            ),
            "category": forms.Select(attrs={"class": "form-select"}),
            "cover_image": forms.ClearableFileInput(attrs={"class": "form-control"}),
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
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Название"}
            ),
            "subtitle": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Подзаголовок"}
            ),
            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Текст статьи",
                    "rows": 10,
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Краткое описание",
                    "rows": 3,
                }
            ),
            "category": forms.Select(attrs={"class": "form-select"}),
            "cover_image": forms.ClearableFileInput(attrs={"class": "form-control"}),
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
