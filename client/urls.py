from django.urls import path
from . import views

app_name = 'Client'

urlpatterns = [
    path('homepage', views.homeView, name = 'home'),
    path('login', views.login, name = 'login'),
    path('landing_page', views.reportView, name = 'viewReport'),
]