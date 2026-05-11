from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="studio_dashboard"),
    # Видео
    path("videos/", views.video_list, name="studio_video_list"),
    path("video/create/", views.video_create, name="studio_video_create"),
    path("video/<int:pk>/edit/", views.video_edit, name="studio_video_edit"),
    path("video/<int:pk>/delete/", views.video_delete, name="studio_video_delete"),
    path(
        "video/create/ajax/", views.video_create_ajax, name="studio_video_create_ajax"
    ),
    # Аудио
    path("audios/", views.audio_list, name="studio_audio_list"),
    path("audio/create/", views.audio_create, name="studio_audio_create"),
    path("audio/<int:pk>/edit/", views.audio_edit, name="studio_audio_edit"),
    path("audio/<int:pk>/delete/", views.audio_delete, name="studio_audio_delete"),
    path(
        "audio/create/ajax/", views.audio_create_ajax, name="studio_audio_create_ajax"
    ),
    # Статьи
    path("texts/", views.text_list, name="studio_text_list"),
    path("text/create/", views.text_create, name="studio_text_create"),
    path("text/<int:pk>/edit/", views.text_edit, name="studio_text_edit"),
    path("text/<int:pk>/delete/", views.text_delete, name="studio_text_delete"),
    path("text/create/ajax/", views.text_create_ajax, name="studio_text_create_ajax"),
    # Курсы
    path("courses/", views.course_list_studio, name="studio_course_list"),
    path("courses/create/", views.course_create, name="studio_course_create"),
    path("courses/<int:pk>/edit/", views.course_edit, name="studio_course_edit"),
    path("courses/<int:pk>/delete/", views.course_delete, name="studio_course_delete"),
]
