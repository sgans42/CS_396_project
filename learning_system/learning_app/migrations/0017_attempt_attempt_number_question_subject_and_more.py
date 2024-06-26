# Generated by Django 4.2.6 on 2023-11-05 21:49

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('learning_app', '0016_attempt'),
    ]

    operations = [
        migrations.AddField(
            model_name='attempt',
            name='attempt_number',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='question',
            name='subject',
            field=models.CharField(default='', max_length=100),
        ),
        migrations.AddField(
            model_name='useranswer',
            name='is_correct',
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=20, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('students', models.ManyToManyField(blank=True, related_name='enrolled_subjects', to=settings.AUTH_USER_MODEL)),
                ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='taught_subjects', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
