# templatetags/exercise_tags.py
from django import template

register = template.Library()

@register.filter
def get_user_answer(user_answers, question_id):
    return user_answers.filter(question_id=question_id).first().choice_id


@register.filter(name='get_item')
def get_item(dictionary, key):
    return dictionary.get(key)
