# Generated by Django 4.2.6 on 2023-10-16 08:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('learning_app', '0003_exercise_author_exercise_content_exercise_date_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='image',
            field=models.ImageField(default='default.png', upload_to='profile_pics'),
        ),
    ]
