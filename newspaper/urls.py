from django.urls import path

from . import views

urlpatterns = [
    # Публичная часть
    path("", views.issue_list, name="newspaper_home"),
    path("<slug:slug>/", views.issue_detail, name="newspaper_issue_detail"),
    # Конструктор газеты (роль «Редактор газеты»)
    path("editor/", views.editor_dashboard, name="newspaper_editor_dashboard"),
    path("editor/issue/create/", views.issue_create, name="newspaper_editor_issue_create"),
    path(
        "editor/issue/<int:pk>/",
        views.issue_edit,
        name="newspaper_editor_issue_edit",
    ),
    path(
        "editor/issue/<int:pk>/delete/",
        views.issue_delete,
        name="newspaper_editor_issue_delete",
    ),
    path(
        "editor/issue/<int:issue_pk>/block/add/",
        views.block_create,
        name="newspaper_editor_block_create",
    ),
    path(
        "editor/block/<int:pk>/edit/",
        views.block_edit,
        name="newspaper_editor_block_edit",
    ),
    path(
        "editor/block/<int:pk>/delete/",
        views.block_delete,
        name="newspaper_editor_block_delete",
    ),
    path(
        "editor/block/<int:pk>/<str:direction>/",
        views.block_move,
        name="newspaper_editor_block_move",
    ),
]
