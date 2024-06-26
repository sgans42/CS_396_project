# Generated by Django 4.2.6 on 2023-10-19 19:35

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('learning_app', '0014_choice_is_correct'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserAnswer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('choice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='learning_app.choice')),
                ('exercise', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='learning_app.exercise')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='learning_app.question')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
