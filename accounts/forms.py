from django import forms
from django.contrib.auth import forms as auth_forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator

from .models import User


class RegistrationForm(UserCreationForm):
    """Форма регистрации пользователя по email с опциональным номером телефона"""

    phone_regex = RegexValidator(
        regex=r"^\+?1?\d{9,15}$", message="Номер телефона в формате: '+79999999999'."
    )
    phone_number = forms.CharField(
        validators=[phone_regex], max_length=17, required=False, label="Номер телефона"
    )

    class Meta(UserCreationForm.Meta):  # type: ignore[name-defined]
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "password1",
            "password2",
        )
        widgets = {  # noqa: RUF012 - словарь виджетов, стандартный паттерн Django
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "Email"}
            ),
            "first_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Имя"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Фамилия"}
            ),
        }

    def __init__(self, *args, **kwargs):
        """Инициализирует форму регистрации и добавляет Bootstrap-классы
        к полям пароля и телефона."""
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Пароль"}
        )
        self.fields["password2"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Подтверждение пароля"}
        )
        self.fields["phone_number"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Телефон"}
        )


class ProfileForm(forms.ModelForm):
    """Форма редактирования профиля пользователя (имя, контакты, аватар, о себе)"""

    phone_regex = RegexValidator(
        regex=r"^\+?1?\d{9,15}$", message="Номер телефона в формате: '+79999999999'."
    )
    phone_number = forms.CharField(
        validators=[phone_regex], max_length=17, required=False, label="Номер телефона"
    )

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "phone_number",
            "avatar",
            "bio",
        )
        widgets = {  # noqa: RUF012 - словарь виджетов, стандартный паттерн Django
            "first_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Имя"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Фамилия"}
            ),
            "phone_number": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "+79999999999"}
            ),
            "avatar": forms.ClearableFileInput(
                attrs={"class": "form-control", "accept": "image/*"}
            ),
            "bio": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Расскажите немного о себе…",
                }
            ),
        }


class PasswordChangeForm(auth_forms.PasswordChangeForm):
    """Форма смены пароля с Bootstrap-классами"""

    def __init__(self, *args, **kwargs):
        """Добавляет класс form-control к полям формы смены пароля."""
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})


class LoginForm(forms.Form):
    """Форма входа пользователя по email и паролю"""

    email = forms.EmailField(
        label="Email", widget=forms.EmailInput(attrs={"autofocus": True})
    )
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        """Инициализирует форму входа и добавляет Bootstrap-классы к полям."""
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Email"}
        )
        self.fields["password"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Пароль"}
        )
