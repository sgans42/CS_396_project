# Generated by Django 4.2.6 on 2023-11-06 01:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('learning_app', '0022_course_enrolled_students'),
    ]

    operations = [
        migrations.AddField(
            model_name='exercise',
            name='course',
            field=models.ForeignKey(default=4, on_delete=django.db.models.deletion.CASCADE, related_name='exercises', to='learning_app.course'),
        ),
        migrations.AddField(
            model_name='lesson',
            name='course',
            field=models.ForeignKey(default=4, on_delete=django.db.models.deletion.CASCADE, related_name='lessons', to='learning_app.course'),
        ),
    ]
