from django.urls import path
from . import views
from rest_framework.documentation import include_docs_urls

urlpatterns = [
    path('', include_docs_urls(title='API Documentation')),
    path('issues', views.issues),
    path('projects', views.projects),
]