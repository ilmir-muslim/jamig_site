from django import forms

from .models import NewspaperBlock, NewspaperIssue


class NewspaperIssueForm(forms.ModelForm):
    """Форма создания и редактирования выпуска газеты в конструкторе"""

    class Meta:
        model = NewspaperIssue
        fields = (
            "title",
            "number",
            "issue_date",
            "cover_image",
            "description",
            "pdf_file",
            "status",
        )
        widgets = {  # noqa: RUF012 - словарь виджетов, стандартный паттерн Django
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Название выпуска"}
            ),
            "number": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Например: 12 (254)"}
            ),
            "issue_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"
            ),
            "cover_image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Анонс для главной страницы",
                    "rows": 3,
                }
            ),
            "pdf_file": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # date input может принимать None (пустое поле), поэтому type: ignore для Pylance
        self.fields["issue_date"].widget.format = "%Y-%m-%d"  # type: ignore[attr-defined]
        self.fields["issue_date"].input_formats = ["%Y-%m-%d"]  # type: ignore[attr-defined]


class NewspaperBlockForm(forms.ModelForm):
    """Форма блока (полосы) выпуска: заголовок, текст, фото с подписью"""

    class Meta:
        model = NewspaperBlock
        fields = (
            "title",
            "subtitle",
            "block_type",
            "content",
            "author_name",
            "photo",
            "photo_caption",
            "order",
        )
        widgets = {  # noqa: RUF012 - словарь виджетов, стандартный паттерн Django
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Заголовок материала"}
            ),
            "subtitle": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Подзаголовок"}
            ),
            "block_type": forms.Select(attrs={"class": "form-select"}),
            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Текст материала. Каждый абзац — с новой строки.",
                    "rows": 10,
                }
            ),
            "author_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "ФИО автора"}
            ),
            "photo": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "photo_caption": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Подпись к фотографии"}
            ),
            "order": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "0 — автоматически (в конец выпуска)",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # В форме добавления нового материала поле порядка скрываем:
        # NewspaperBlock.save() сам рассчитает его (блок встанет в конец выпуска).
        if self.instance.pk is None:
            self.fields.pop("order", None)
