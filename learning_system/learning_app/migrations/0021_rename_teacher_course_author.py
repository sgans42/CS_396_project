# Generated by Django 4.2.6 on 2023-11-05 23:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('learning_app', '0020_remove_course_exercises_remove_course_lessons_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='course',
            old_name='teacher',
            new_name='author',
        ),
    ]
