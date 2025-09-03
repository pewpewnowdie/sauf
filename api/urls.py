from django.urls import path
from . import views

urlpatterns = [
    path('issues', views.issues),
    path('projects', views.projects),
]