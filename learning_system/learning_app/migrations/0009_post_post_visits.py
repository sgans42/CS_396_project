# Generated by Django 4.2.6 on 2023-10-16 16:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('learning_app', '0008_rename_created_by_lesson_author'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='post_visits',
            field=models.IntegerField(default=0),
        ),
    ]