from django.contrib import admin
from .models import Post, Profile, Lesson, Exercise, Course, Subject

# Register your models here.

admin.site.register(Post)
admin.site.register(Profile)
admin.site.register(Lesson)
admin.site.register(Exercise)
admin.site.register(Course)
admin.site.register(Subject)

