from django.urls import path
from . import views

app_name = 'Client'

urlpatterns = [
    path('', views.general_views.homeView, name = 'home'),
    path('login', views.general_views.ClientLogin, name = 'login'),
    path('logout', views.general_views.ClientLogoutView.as_view(), name = 'logout'),
    path('classification/Overall Accuracy', views.classification_views.overallAccuracyView, name = 'classification_overallAccuracy'),
    path('classification/Model Accuracy', views.classification_views.modelAccuracyView, name = 'classification_modelAccuracy'),
    path('classification/Model Inclusivity', views.classification_views.modelInclusivityView, name = 'classification_modelInclusivity'),
    path('about/', views.general_views.aboutView, name='about'),
    path('regression/Overall Accuracy', views.regression_views.overallAccuracyView, name = 'regression_overallAccuracy'),
    path('regression/Model Accuracy', views.regression_views.modelAccuracyView, name = 'regression_modelAccuracy'),
    path('regression/Model Inclusivity', views.regression_views.modelInclusivityView, name = 'regression_modelInclusivity'),
]