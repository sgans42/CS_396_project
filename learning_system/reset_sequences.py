# reset_sequences.py

from django import setup
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learning_system.settings')
setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='learning_app_attempt'")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='learning_app_useranswer'")
