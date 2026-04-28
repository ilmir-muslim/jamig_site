from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="studio_dashboard"),
    path("video/create/", views.video_create, name="studio_video_create"),
    path("video/<int:pk>/edit/", views.video_edit, name="studio_video_edit"),
    path("video/<int:pk>/delete/", views.video_delete, name="studio_video_delete"),
    path("audio/create/", views.audio_create, name="studio_audio_create"),
    path("audio/<int:pk>/edit/", views.audio_edit, name="studio_audio_edit"),
    path("audio/<int:pk>/delete/", views.audio_delete, name="studio_audio_delete"),
    path("text/create/", views.text_create, name="studio_text_create"),
    path("text/<int:pk>/edit/", views.text_edit, name="studio_text_edit"),
    path("text/<int:pk>/delete/", views.text_delete, name="studio_text_delete"),
]
