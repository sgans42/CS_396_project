from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, Reply, Question, Choice, Course, Subject, ExerciseCategory
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


class PostSearchForm(forms.Form):
    search_query = forms.CharField(required=False, label='Search Posts')



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
    course = forms.ModelChoiceField(queryset=Course.objects.none(), required=False, label="Select a Course")
    category = forms.ModelChoiceField(queryset=ExerciseCategory.objects.none(), required=False, label="Select a Category")

    class Meta:
        model = Exercise
        fields = ['title', 'content', 'course', 'category']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(ExerciseForm, self).__init__(*args, **kwargs)

        if user:
            self.fields['course'].queryset = Course.objects.filter(author=user)

        if 'course' in self.data:
            try:
                course_id = int(self.data.get('course'))
                self.fields['category'].queryset = ExerciseCategory.objects.filter(courses__id=course_id)
                print(f"Initializing form with POST data, course_id: {course_id}")
            except (ValueError, TypeError):
                self.fields['category'].queryset = ExerciseCategory.objects.none()
        elif self.instance.pk and self.instance.course:
            self.fields['category'].queryset = self.instance.course.categories.all()
            print(f"Initializing form with instance data, course: {self.instance.course}")
        else:
            self.fields['category'].queryset = ExerciseCategory.objects.none()


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
    num_categories = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = Course
        fields = ['subject', 'code', 'title', 'description', 'num_categories']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['num_categories'].initial = self.instance.categories.count()
            for idx, category in enumerate(self.instance.categories.all(), start=1):
                self.fields[f'category_name_{idx}'] = forms.CharField(
                    initial=category.name,
                    required=False
                )
                self.fields[f'category_weight_{idx}'] = forms.DecimalField(
                    initial=category.weight,
                    max_digits=4,
                    decimal_places=2,
                    required=False
                )
                self.fields[f'category_delete_{idx}'] = forms.BooleanField(
                    required=False,
                    label='Delete this category'
                )


class ExerciseCategoryForm(forms.ModelForm):
    class Meta:
        model = ExerciseCategory
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super(ExerciseCategoryForm, self).__init__(*args, **kwargs)  # Corrected use of super()
        # You can add custom initialization logic if needed


class WeightAdjustmentForm(forms.Form):
    def __init__(self, *args, **kwargs):
        course_id = kwargs.pop('course_id', None)
        super().__init__(*args, **kwargs)
        if course_id:
            categories = ExerciseCategory.objects.filter(exercises__course__id=course_id).distinct()
            for category in categories:
                field_name = f'weight_{category.id}'
                self.fields[field_name] = forms.IntegerField(
                    min_value=0,
                    max_value=100,
                    required=True,
                    initial=category.weight,
                    label=f'{category.name} Weight'
                )
