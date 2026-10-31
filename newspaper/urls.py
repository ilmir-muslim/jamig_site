from django.urls import path

from . import views

urlpatterns = [
    # Публичная часть.
    # NB: маршруты конструктора (/newspaper/editor/...) подключаются в
    # jamig_site/urls.py отдельным префиксом до этого include (см. newspaper/editor_urls.py),
    # иначе catch-all <slug:slug>/ перехватывал бы "/newspaper/editor/" и отдавал 404.
    path("", views.issue_list, name="newspaper_home"),
    path("<slug:slug>/", views.issue_detail, name="newspaper_issue_detail"),
]
