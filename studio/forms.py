from django import forms
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
            "description": forms.Textarea(attrs={"rows": 3}),
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
            "description": forms.Textarea(attrs={"rows": 3}),
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
            "content": forms.Textarea(attrs={"rows": 10}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }
