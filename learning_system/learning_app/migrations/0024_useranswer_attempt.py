# Generated by Django 4.2.6 on 2023-11-06 23:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('learning_app', '0023_exercise_course_lesson_course'),
    ]

    operations = [
        migrations.AddField(
            model_name='useranswer',
            name='attempt',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, to='learning_app.attempt'),
        ),
    ]
