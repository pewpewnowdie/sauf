from django.contrib import admin
from .models import User, Project, Version, User_Project, Sprint, Issue

# Register your models here.
admin.site.register(User)
admin.site.register(Project)
admin.site.register(Version)
admin.site.register(User_Project)
admin.site.register(Sprint)
admin.site.register(Issue)
