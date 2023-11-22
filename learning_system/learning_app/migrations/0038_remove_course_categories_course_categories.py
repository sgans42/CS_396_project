# Generated by Django 4.2.6 on 2023-11-22 19:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('learning_app', '0037_rename_category_course_categories'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='course',
            name='categories',
        ),
        migrations.AddField(
            model_name='course',
            name='categories',
            field=models.ManyToManyField(blank=True, related_name='courses', to='learning_app.exercisecategory'),
        ),
    ]