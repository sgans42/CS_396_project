# Generated by Django 4.2.6 on 2023-10-18 02:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('learning_app', '0011_rename_text_choice_choice_text_alter_exercise_author_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='submission',
            name='exercise',
        ),
        migrations.RemoveField(
            model_name='submission',
            name='student',
        ),
        migrations.RenameField(
            model_name='question',
            old_name='text',
            new_name='question_text',
        ),
        migrations.RemoveField(
            model_name='choice',
            name='is_correct',
        ),
        migrations.AddField(
            model_name='question',
            name='question_type',
            field=models.CharField(choices=[('TEXT', 'Open-ended'), ('MC', 'Multiple choice')], default='TEXT', max_length=4),
        ),
        migrations.DeleteModel(
            name='Result',
        ),
        migrations.DeleteModel(
            name='Submission',
        ),
    ]
