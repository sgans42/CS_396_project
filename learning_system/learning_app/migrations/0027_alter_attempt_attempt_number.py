# Generated by Django 4.2.6 on 2023-11-06 23:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('learning_app', '0026_alter_useranswer_attempt'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attempt',
            name='attempt_number',
            field=models.IntegerField(),
        ),
    ]
