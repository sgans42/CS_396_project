from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, Reply, Question, Choice, Course, Subject
from .models import Post, Lesson, Exercise


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    role = forms.ChoiceField(choices=[('TEACHER', 'Teacher'), ('STUDENT', 'Student')])
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()
    class Meta:
        model = User
        fields = ['username', 'email']


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image']


class ReplyForm(forms.ModelForm):
    class Meta:
        model = Reply
        fields = ['content']


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'uploaded_file']


class LessonForm(forms.ModelForm):
    course = forms.ModelChoiceField(queryset=Course.objects.all(), required=False, label="Select a Course")

    class Meta:
        model = Lesson
        fields = ['title', 'content', 'document', 'video', 'animation', 'course']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(LessonForm, self).__init__(*args, **kwargs)
        if user is not None:
            self.fields['course'].queryset = Course.objects.filter(author=user)


class ExerciseForm(forms.ModelForm):
    course = forms.ModelChoiceField(queryset=Course.objects.all(), required=False, label="Select a Course")

    class Meta:
        model = Exercise
        fields = ['title', 'content', 'date', 'course']

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['question_text']

class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ['choice_text', 'is_correct']

QuestionFormSet = forms.modelformset_factory(Question, form=QuestionForm, extra=10)
ChoiceFormSet = forms.modelformset_factory(Choice, form=ChoiceForm, extra=4)
UpdateChoiceFormSet = forms.modelformset_factory(Choice, form=ChoiceForm, extra=0)


class QuizForm(forms.Form):

    def __init__(self, *args, **kwargs):
        exercise = kwargs.pop('exercise')
        super(QuizForm, self).__init__(*args, **kwargs)

        for question in exercise.questions.all():
            choice_list = [(choice.id, choice.choice_text) for choice in question.choices.all()]
            self.fields[f'question_{question.id}'] = forms.ChoiceField(
                choices=choice_list,
                widget=forms.RadioSelect,
                label=question.question_text
            )

#Courses functions ---------------------------------------------------------------------------->


class CourseSearchForm(forms.Form):
    query = forms.CharField(required=False, label='Search Courses')


class CourseSelectForm(forms.Form):
    course = forms.ModelChoiceField(queryset=Course.objects.none(), required=True, label="Select a Course")

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['course'].queryset = Course.objects.filter(author=user)


class CourseForm(forms.ModelForm):
    subject = forms.ModelChoiceField(queryset=Subject.objects.all(), required=False)

    class Meta:
        model = Course
        fields = ['subject', 'code', 'title', 'description']

    def __init__(self, *args, **kwargs):
        super(CourseForm, self).__init__(*args, **kwargs)
        self.fields['subject'].initial = Subject.get_default_subject()


