from django.urls import path
from . import views

app_name = 'Client'

urlpatterns = [
    path('', views.homeView, name = 'home'),
    path('login', views.ClientLogin, name = 'login'),
    path('logout', views.ClientLogoutView.as_view(), name = 'logout'),
    path('Overall Accuracy', views.overallAccuracyView, name = 'overallAccuracy'),
    path('Model Accuracy', views.modelAccuracyView, name = 'modelAccuracy'),
    path('Model Inclusivity', views.modelInclusivityView, name = 'modelInclusivity'),
    path('about/', views.aboutView, name='about'),
]