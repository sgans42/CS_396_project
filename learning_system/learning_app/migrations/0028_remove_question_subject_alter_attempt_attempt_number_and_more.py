# Generated by Django 4.2.6 on 2023-11-06 23:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('learning_app', '0027_alter_attempt_attempt_number'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='question',
            name='subject',
        ),
        migrations.AlterField(
            model_name='attempt',
            name='attempt_number',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='exercise',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exercises', to='learning_app.course'),
        ),
        migrations.AlterField(
            model_name='lesson',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lessons', to='learning_app.course'),
        ),
        migrations.AlterField(
            model_name='useranswer',
            name='attempt',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, to='learning_app.attempt'),
        ),
    ]