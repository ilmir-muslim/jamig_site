from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("authors/", views.author_list, name="author_list"),
    path("author/<int:pk>/", views.author_detail, name="author_detail"),
]
