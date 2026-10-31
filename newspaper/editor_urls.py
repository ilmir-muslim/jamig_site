from django.urls import path

from . import views

# Маршруты конструктора газеты.
# Подключаются в jamig_site/urls.py отдельным префиксом "newspaper/editor/",
# чтобы не перекрываться с публичным catch-all маршрутом <slug:slug>/
# из newspaper/urls.py (иначе /newspaper/editor/ попадало на страницу выпуска
# и давало 404 "No NewspaperIssue matches the given query").

urlpatterns = [
    path("", views.editor_dashboard, name="newspaper_editor_dashboard"),
    path("issue/create/", views.issue_create, name="newspaper_editor_issue_create"),
    path(
        "issue/<int:pk>/",
        views.issue_edit,
        name="newspaper_editor_issue_edit",
    ),
    path(
        "issue/<int:pk>/delete/",
        views.issue_delete,
        name="newspaper_editor_issue_delete",
    ),
    path(
        "issue/<int:pk>/export-pdf/",
        views.issue_export_pdf,
        name="newspaper_editor_issue_export_pdf",
    ),
    path(
        "issue/<int:issue_pk>/block/add/",
        views.block_create,
        name="newspaper_editor_block_create",
    ),
    path(
        "block/<int:pk>/edit/",
        views.block_edit,
        name="newspaper_editor_block_edit",
    ),
    path(
        "block/<int:pk>/duplicate/",
        views.block_duplicate,
        name="newspaper_editor_block_duplicate",
    ),
    path(
        "block/<int:pk>/delete/",
        views.block_delete,
        name="newspaper_editor_block_delete",
    ),
    path(
        "block/<int:pk>/gallery/add/",
        views.gallery_add,
        name="newspaper_editor_gallery_add",
    ),
    path(
        "block/<int:pk>/gallery/remove/",
        views.gallery_remove,
        name="newspaper_editor_gallery_remove",
    ),
    path(
        "block/<int:pk>/<str:direction>/",
        views.block_move,
        name="newspaper_editor_block_move",
    ),
]
