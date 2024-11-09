from django.urls import path
from . import views

app_name = 'Client'

urlpatterns = [
    path('homepage', views.homeView, name = 'home'),
    path('login', views.login, name = 'login'),
    path('Overall Accuracy', views.overallAccuracyView, name = 'overallAccuracy'),
]