# materials/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("videos/", views.VideoListView.as_view(), name="video_list"),
    path("videos/<slug:slug>/", views.VideoDetailView.as_view(), name="video_detail"),
    path("audios/", views.AudioListView.as_view(), name="audio_list"),
    path("audios/<slug:slug>/", views.AudioDetailView.as_view(), name="audio_detail"),
    path("texts/", views.TextListView.as_view(), name="text_list"),
    path("texts/<slug:slug>/reader/", views.reader_view, name="text_reader"),
    path("texts/save-progress/", views.save_progress, name="save_progress"),
]
