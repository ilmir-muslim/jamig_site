from django import forms

from .models import NewspaperBlock, NewspaperIssue, NewspaperSettings


class MultipleFileInput(forms.FileInput):
    """Виджет загрузки нескольких файлов (Django >= 4.2 требует явный флаг)."""

    allow_multiple_selected = True


class NewspaperSettingsForm(forms.ModelForm):
    """Настройки газеты: название издания, выходные данные, полосность."""

    class Meta:
        model = NewspaperSettings
        fields = ("publication_name", "tagline", "founder", "address", "print_pages")
        widgets = {  # noqa: RUF012 - словарь виджетов, стандартный паттерн Django
            "publication_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Газета мечети Джамиг"}
            ),
            "tagline": forms.TextInput(attrs={"class": "form-control"}),
            "founder": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "print_pages": forms.NumberInput(
                attrs={"class": "form-control", "min": 4, "step": 4}
            ),
        }


class NewspaperIssueForm(forms.ModelForm):
    """Форма создания и редактирования выпуска газеты в конструкторе"""

    clear_announce = forms.BooleanField(
        required=False,
        label="Сбросить ручной анонс",
        help_text="Отметьте, чтобы анонс снова формировался автоматически из первой полосы.",
    )
    # Отдельные чекбоксы вместо встроенного «clear» у ClearableFileInput:
    # Django не даёт одновременно отметить «очистить» и приложить новый файл,
    # а обычному пользователю это и не нужно — загрузка нового файла сама
    # заменяет старый. Ошибки вида "submit a file or check the clear checkbox"
    # больше не появится.
    clear_cover_image = forms.BooleanField(
        required=False,
        initial=False,
        label="Удалить обложку",
        help_text="Отметьте, чтобы убрать текущую обложку выпуска.",
    )
    clear_pdf_file = forms.BooleanField(
        required=False,
        initial=False,
        label="Удалить PDF-файл",
        help_text="Отметьте, чтобы убрать загруженный PDF (например, перед загрузкой нового).",
    )

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
            "cover_image": forms.FileInput(attrs={"class": "form-control", "accept": "image/*"}),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": (
                        "Не заполняйте — анонс соберётся автоматически из первой полосы"
                    ),
                    "rows": 3,
                }
            ),
            "pdf_file": forms.FileInput(attrs={"class": "form-control", "accept": "application/pdf"}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # date input может принимать None (пустое поле), поэтому type: ignore для Pylance
        self.fields["issue_date"].widget.format = "%Y-%m-%d"  # type: ignore[attr-defined]
        self.fields["issue_date"].input_formats = ["%Y-%m-%d"]  # type: ignore[attr-defined]
        if "clear_announce" in self.fields:
            self.fields["clear_announce"].widget.attrs["class"] = "form-check-input"

    def clean_pdf_file(self):
        pdf = self.cleaned_data.get("pdf_file")
        if pdf:
            name = getattr(pdf, "name", "") or ""
            if not name.lower().endswith(".pdf"):
                raise forms.ValidationError(
                    "Можно загружать только файлы в формате PDF. "
                    "Выберите файл с расширением .pdf или оставьте поле пустым."
                )
        return pdf

    def save(self, commit=True):
        issue = super().save(commit=False)
        if self.cleaned_data.get("clear_announce"):
            issue.description = ""
        # Чекбоксы «удалить» применяются только когда новый файл не приложен —
        # иначе новая загрузка автоматически заменяет старый файл.
        if self.cleaned_data.get("clear_cover_image") and not self.files.get("cover_image"):
            if issue.cover_image:
                issue.cover_image.delete(save=False)
        if self.cleaned_data.get("clear_pdf_file") and not self.files.get("pdf_file"):
            if issue.pdf_file:
                issue.pdf_file.delete(save=False)
        if commit:
            issue.save()
        return issue


class NewspaperBlockForm(forms.ModelForm):
    """Форма материала (полосы) выпуска: заголовки, текст с разметкой, фото"""

    extra_photos = forms.FileField(
        required=False,
        label="Дополнительные фотографии",
        widget=MultipleFileInput(
            attrs={"class": "form-control", "accept": "image/*"}
        ),
        help_text="Можно выбрать несколько файлов — они попадут в галерею материала.",
    )

    class Meta:
        model = NewspaperBlock
        fields = (
            "title",
            "subtitle",
            "block_type",
            "size",
            "content",
            "author_name",
            "photo",
            "photo_caption",
            "photo_width",
            "is_front_page",
            "advertiser_name",
            "advertiser_contact",
            "ad_price",
            "ad_discount",
            "ad_volume",
            "ad_paid",
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
            "size": forms.Select(attrs={"class": "form-select"}),
            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": (
                        "Начните печатать статью. Первый абзац станет анонсом на главной.\n\n"
                        "Новый абзац — просто с новой строки."
                    ),
                    "rows": 14,
                }
            ),
            "author_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "ФИО автора"}
            ),
            "photo": forms.FileInput(attrs={"class": "form-control", "accept": "image/*"}),
            "photo_caption": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Подпись к фотографии"}
            ),
            "photo_width": forms.Select(attrs={"class": "form-select"}),
            "is_front_page": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "advertiser_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Название организации или ФИО"}
            ),
            "advertiser_contact": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Телефон, адрес, сайт"}
            ),
            "ad_price": forms.NumberInput(
                attrs={"class": "form-control", "min": 0, "step": "0.01"}
            ),
            "ad_discount": forms.NumberInput(
                attrs={"class": "form-control", "min": 0, "max": 100, "step": 1}
            ),
            "ad_volume": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Например: 1/4 полосы"}
            ),
            "ad_paid": forms.CheckboxInput(attrs={"class": "form-check-input"}),
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
        block_type = (
            self.data.get("block_type") if self.is_bound else self.instance.block_type
        ) or "article"
        # Рекламные поля нужны только для объявлений — скрываем остальные,
        # чтобы не путать редактора.
        for name in (
            "advertiser_name",
            "advertiser_contact",
            "ad_price",
            "ad_discount",
            "ad_volume",
            "ad_paid",
        ):
            self.fields[name].required = False
            widget_attrs = self.fields[name].widget.attrs
            widget_attrs.setdefault("data-ad-field", name)
            if block_type != "ad":
                widget_attrs["hidden"] = "hidden"
        if block_type == "ad":
            self.fields["author_name"].label = "Автор объявления (необязательно)"

    def get_all_extra_photos(self):
        """Возвращает ВСЕ файлы, загруженные в поле extra_photos (multiple=True)."""
        files = getattr(self, "files", None)
        if not files or not hasattr(files, "getlist"):
            return []
        result = []
        for f in files.getlist("extra_photos"):
            content_type = getattr(f, "content_type", "") or ""
            if not content_type.startswith("image/"):
                continue
            result.append(f)
        return result

    def clean_extra_photos(self):
        # Проверка типов выполняется в get_all_extra_photos; здесь — совместимость.
        files = self.cleaned_data.get("extra_photos")
        if isinstance(files, (list, tuple)):
            return list(files)
        return [files] if files else []
