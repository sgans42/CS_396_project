# Generated by Django 4.2.6 on 2023-11-13 10:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('learning_app', '0029_question_subject_alter_exercise_course_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='useranswer',
            name='attempt',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='learning_app.attempt'),
        ),
    ]
