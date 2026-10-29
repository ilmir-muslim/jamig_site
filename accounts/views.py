from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render

from .forms import LoginForm, RegistrationForm


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
