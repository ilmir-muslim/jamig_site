from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('set-city/', views.set_city, name='set_city'),

]