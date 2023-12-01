# Generated by Django 4.2.7 on 2023-11-25 19:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('learning_app', '0039_exercise_categories'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='a_grade_min',
            field=models.DecimalField(decimal_places=2, default=90.0, max_digits=5),
        ),
        migrations.AddField(
            model_name='course',
            name='b_grade_min',
            field=models.DecimalField(decimal_places=2, default=80.0, max_digits=5),
        ),
        migrations.AddField(
            model_name='course',
            name='c_grade_min',
            field=models.DecimalField(decimal_places=2, default=70.0, max_digits=5),
        ),
        migrations.AddField(
            model_name='course',
            name='d_grade_min',
            field=models.DecimalField(decimal_places=2, default=60.0, max_digits=5),
        ),
    ]