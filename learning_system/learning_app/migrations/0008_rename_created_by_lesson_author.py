# Generated by Django 4.2.6 on 2023-10-16 16:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('learning_app', '0007_lesson_animation_lesson_document_lesson_video'),
    ]

    operations = [
        migrations.RenameField(
            model_name='lesson',
            old_name='created_by',
            new_name='author',
        ),
    ]