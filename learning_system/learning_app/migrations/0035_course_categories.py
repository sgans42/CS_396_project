# Generated by Django 4.2.6 on 2023-11-22 14:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('learning_app', '0034_remove_course_categories_alter_exercisecategory_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='categories',
            field=models.ManyToManyField(blank=True, related_name='courses', to='learning_app.exercisecategory'),
        ),
    ]
