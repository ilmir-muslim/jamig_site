from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import LoginForm, PasswordChangeForm, ProfileForm, RegistrationForm


def register(request):
    """Регистрация нового пользователя: создаёт аккаунт, авторизует его
    и перенаправляет на главную страницу. Если пользователь уже авторизован — редирект на главную."""
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Добро пожаловать, {user.first_name}!")
            return redirect("home")
    else:
        form = RegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


def user_login(request):
    """Вход в систему по email и паролю. Авторов перенаправляет в студию,
    остальных — на главную страницу."""
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"С возвращением, {user.first_name}!")
                # Перенаправляем на студию, если автор
                if getattr(request.user, "user_type", None) == "employee":
                    return redirect("studio_dashboard")
                return redirect("home")
            else:
                messages.error(request, "Неверный email или пароль.")
    else:
        form = LoginForm()
    return render(request, "accounts/login.html", {"form": form})


def user_logout(request):
    """Выход пользователя из системы с показом информационного сообщения."""
    logout(request)
    messages.info(request, "Вы вышли из системы.")
    return redirect("home")


@login_required
def profile(request):
    """Страница профиля: просмотр и редактирование данных пользователя
    (имя, телефон, аватар, «о себе»), а также смена пароля."""
    if request.method == "POST":
        if "save_profile" in request.POST:
            form = ProfileForm(request.POST, request.FILES, instance=request.user)
            password_form = PasswordChangeForm(request.user)
            if form.is_valid():
                form.save()
                messages.success(request, "Профиль успешно обновлён.")
                return redirect("profile")
        elif "change_password" in request.POST:
            form = ProfileForm(instance=request.user)
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Пароль успешно изменён.")
                return redirect("profile")
        else:
            form = ProfileForm(instance=request.user)
            password_form = PasswordChangeForm(request.user)
    else:
        form = ProfileForm(instance=request.user)
        password_form = PasswordChangeForm(request.user)

    return render(
        request,
        "accounts/profile.html",
        {"form": form, "password_form": password_form},
    )
