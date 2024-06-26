# Generated by Django 4.2.6 on 2023-11-22 19:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('learning_app', '0035_course_categories'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='course',
            name='categories',
        ),
        migrations.RemoveField(
            model_name='exercisecategory',
            name='exercises',
        ),
        migrations.AddField(
            model_name='course',
            name='category',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='exercises', to='learning_app.exercisecategory'),
        ),
        migrations.AlterField(
            model_name='exercise',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exercises', to='learning_app.course'),
        ),
    ]
