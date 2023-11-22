from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import transaction
from django.db.models import Max, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views import View

from .models import (Post, Reply, Lesson, Exercise, Question, Choice, UserAnswer, Attempt, Course, Subject, Profile,
                     ExerciseCategory)
from django.contrib import messages
from .forms import (UserRegisterForm, UserUpdateForm, ProfileUpdateForm, ReplyForm, LessonForm, ExerciseForm,
                    QuestionFormSet, ChoiceFormSet, QuizForm, CourseSearchForm, CourseForm, CourseSelectForm,
                    UpdateChoiceFormSet, PostSearchForm, ExerciseCategoryForm
                    )
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .forms import PostForm
from django import forms
from django.http import HttpResponseRedirect, Http404
from django.db import models


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()

            role = form.cleaned_data.get('role')

            profile, created = Profile.objects.update_or_create(
                user=user,
                defaults={'role': role},
            )

            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=user.username, password=raw_password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Account created for {user.username} with the role of {profile.role}.')
                return redirect('learning_app-home')
    else:
        form = UserRegisterForm()
    return render(request, 'learning_app/register.html', {'form': form})


@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Your account has been updated!')
            return redirect('../profile/')

    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }
    return render(request, 'learning_app/profile.html', context)


# All User interactions -------------------------------------------------------------------------- User interactions ->
class UserPostListView(ListView):
    model = Post
    template_name = 'learning_app/user_posts.html'  # <app>/<model>_<viewtype>.html
    context_object_name = 'posts'

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        return Post.objects.filter(author=user).order_by('-date')


class UserLessonListView(ListView):
    model = Lesson
    template_name = 'learning_app/user_lesson.html'  # <app>/<model>_<viewtype>.html
    context_object_name = 'lessons'

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        return Lesson.objects.filter(author=user).order_by('-date')


class UserExerciseListView(ListView):
    model = Exercise
    template_name = 'learning_app/user_exercise.html'  # <app>/<model>_<viewtype>.html
    context_object_name = 'exercises'

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        return Exercise.objects.filter(author=user).order_by('-date')


class StudentCourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'learning_app/student_courses.html'
    context_object_name = 'courses'

    def get_queryset(self):
        return self.request.user.enrolled_courses.all()


class TeacherCourseListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Course
    template_name = 'learning_app/teacher_courses.html'
    context_object_name = 'courses'

    def get_queryset(self):
        return Course.objects.filter(author=self.request.user)

    def test_func(self):
        return self.request.user.profile.role == 'TEACHER'



# All of the Post methods ----------------------------------------------------------------------------- Post methods ->
class PostListView(ListView):
    model = Post
    template_name = 'learning_app/home.html'
    context_object_name = 'posts'

    def get_ordering(self):
        ordering = '-date'
        current_ordering = 'newest'

        if 'ordering' in self.request.GET:
            selected_ordering = self.request.GET['ordering']
            if selected_ordering == 'oldest':
                ordering = 'date'
                current_ordering = 'oldest'
            elif selected_ordering == 'most_views':
                ordering = '-post_visits'
                current_ordering = 'most_views'

        self.current_ordering = current_ordering
        return ordering

    def get_queryset(self):
        queryset = super().get_queryset().order_by(self.get_ordering())
        search_query = self.request.GET.get('search_query', '')

        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        items_per_page = self.request.GET.get('items_per_page', 10)
        current_items_per_page = int(items_per_page)

        paginator = Paginator(self.get_queryset(), current_items_per_page)
        page = self.request.GET.get('page')

        try:
            posts = paginator.page(page)
        except PageNotAnInteger:
            posts = paginator.page(1)
        except EmptyPage:
            posts = paginator.page(paginator.num_pages)

        context['page_obj'] = posts
        context['current_items_per_page'] = current_items_per_page
        context['current_ordering'] = self.current_ordering
        context['search_form'] = PostSearchForm(self.request.GET or None)
        return context


class PostDetailView(DetailView):
    model = Post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ReplyForm()
        context['replies'] = Reply.objects.filter(post=self.object).order_by('-date')
        return context

    def post(self, request, *args, **kwargs):
        form = ReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.post = self.get_object()
            reply.author = request.user
            reply.save()
            return HttpResponseRedirect(reverse('post-detail', kwargs={'pk': self.get_object().pk}))
        return self.get(request, *args, **kwargs)

    def get_object(self):
        obj = super().get_object()
        obj.post_visits += 1
        obj.save()
        return obj



class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.save()
        return super().form_valid(form)


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.save()
        return super().form_valid(form)

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        return False


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    success_url = '/'

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        return False

# All of the Lessons methods -------------------------------------------------------------------- Lessons methods ->
class LessonListView(ListView):
    model = Lesson
    template_name = 'learning_app/lesson.html'
    context_object_name = 'lessons'
    ordering = ['-date']

    def get_queryset(self):
        queryset = super().get_queryset().order_by('-date')
        search_query = self.request.GET.get('search_query', '')

        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query)
            )

        return queryset



class LessonDetailView(DetailView):
    model = Lesson


class LessonCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Lesson
    form_class = LessonForm
    success_url = '/lesson'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def test_func(self):
        return self.request.user.profile.role == 'TEACHER'

    def handle_no_permission(self):
        return redirect('../../lesson')


class LessonUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Lesson
    form_class = LessonForm
    success_url = '/lesson'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.save()
        return super().form_valid(form)

    def test_func(self):
        lesson = self.get_object()
        if self.request.user == lesson.author:
            return True
        return False


class LessonDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Lesson
    success_url = '/lesson'

    def test_func(self):
        lesson = self.get_object()
        if self.request.user == lesson.author:
            return True
        return False

# All of the Exercise methods -------------------------------------------------------------------- Exercise methods ->

class ExerciseListView(ListView):
    model = Exercise
    template_name = 'learning_app/exercise.html'
    context_object_name = 'exercises'
    ordering = ['-date']

    def get_queryset(self):
        queryset = super().get_queryset().order_by('-date')
        search_query = self.request.GET.get('search_query', '')

        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query)
            )

        return queryset



class ExerciseDetailView(LoginRequiredMixin, DetailView):
    model = Exercise
    template_name = 'learning_app/exercise_detail.html'
    context_object_name = 'exercise'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        previous_attempts = Attempt.objects.filter(
            user=self.request.user,
            exercise=self.object
        ).order_by('-date')

        highest_score = previous_attempts.aggregate(max_score=Max('score'))['max_score']

        for attempt in previous_attempts:
            total_questions = self.object.questions.count()
            attempt.percentage = (attempt.score / total_questions) * 100 if total_questions > 0 else 0

        context['previous_attempts'] = previous_attempts
        context['highest_score'] = highest_score if highest_score is not None else "No attempts yet"

        return context


class TakeExerciseDetailView(LoginRequiredMixin, DetailView):
    model = Exercise
    template_name = 'learning_app/exercise_take_detail.html'
    context_object_name = 'exercise'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = QuizForm(exercise=self.object)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        exercise = self.get_object()
        form = QuizForm(request.POST, exercise=exercise)

        attempt_count = Attempt.objects.filter(user=request.user, exercise=exercise).count()
        if attempt_count >= 3:
            messages.error(request, "You have already made the maximum number of attempts for this exercise.")
            return self.get(request, *args, **kwargs)




        if form.is_valid():
            score = 0

            # Create Attempt first
            new_attempt = Attempt.objects.create(user=request.user, exercise=exercise, score=0)

            for question in exercise.questions.all():
                question_field = f'question_{question.id}'
                chosen_answer_id = form.cleaned_data[question_field]
                chosen_answer = get_object_or_404(Choice, pk=chosen_answer_id)

                UserAnswer.objects.create(
                    user=request.user,
                    exercise=exercise,
                    question=question,
                    choice=chosen_answer,
                    is_correct=chosen_answer.is_correct,
                    attempt=new_attempt
                )
                if chosen_answer.is_correct:
                    score += 1

            new_attempt.score = score
            new_attempt.save()

            messages.success(request, "Your attempt has been recorded successfully.")
            return HttpResponseRedirect(reverse('exercise-detail', args=[exercise.id]))
        else:
            messages.error(request, "There was an error with your submission.")
            return self.get(request, *args, **kwargs)


class ExerciseCreateView(LoginRequiredMixin, CreateView):
    model = Exercise
    form_class = ExerciseForm
    template_name = 'learning_app/exercise_form.html'
    success_url = reverse_lazy('exercise')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['user_courses'] = Course.objects.filter(author=self.request.user).prefetch_related('categories')

        if self.request.POST:
            data['questions'] = QuestionFormSet(self.request.POST)
            data['choices'] = [ChoiceFormSet(self.request.POST, prefix=str(x), queryset=Choice.objects.none()) for x in range(0, 10)]
        else:
            data['questions'] = QuestionFormSet(queryset=Question.objects.none())
            data['choices'] = [ChoiceFormSet(prefix=str(x), queryset=Choice.objects.none()) for x in range(0, 10)]

        data['questions_choices'] = zip(data['questions'], data['choices'])
        return data

    def form_valid(self, form):
        exercise = form.save(commit=False)
        exercise.author = self.request.user

        course_category = self.request.POST.get('course_category')
        if course_category:
            course_id, category_id = map(int, course_category.split('_'))
            course = Course.objects.get(id=course_id)
            category = ExerciseCategory.objects.get(id=category_id)
            exercise.course = course
            exercise.save()
            exercise.categories.add(category)

        context = self.get_context_data()
        questions = context['questions']
        if questions.is_valid():
            with transaction.atomic():
                self.object = exercise
                question_instances = questions.save(commit=False)
                for question in question_instances:
                    question.exercise = self.object
                    question.save()
                for choice_formset in context['choices']:
                    if choice_formset.is_valid():
                        choice_instances = choice_formset.save(commit=False)
                        for choice in choice_instances:
                            choice.question = question
                            choice.save()
        return super().form_valid(form)


class ExerciseUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Exercise
    form_class = ExerciseForm
    template_name = 'learning_app/exercise_form.html'
    success_url = reverse_lazy('exercise_list')

    def get_form_kwargs(self):
        kwargs = super(ExerciseUpdateView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['user_courses'] = Course.objects.filter(author=self.request.user).prefetch_related('categories')

        if self.request.POST:
            data['questions'] = QuestionFormSet(self.request.POST, queryset=Question.objects.filter(exercise=self.object))
            data['choices'] = [
                UpdateChoiceFormSet(self.request.POST, prefix=str(x), queryset=Choice.objects.filter(question=question))
                for x, question in enumerate(self.object.questions.all())]
        else:
            data['questions'] = QuestionFormSet(queryset=Question.objects.filter(exercise=self.object))
            data['choices'] = [
                UpdateChoiceFormSet(prefix=str(x), queryset=Choice.objects.filter(question=question))
                for x, question in enumerate(self.object.questions.all())]

        data['questions_choices'] = zip(data['questions'], data['choices'])
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        questions = context['questions']
        choices = context['choices']

        with transaction.atomic():
            self.object = form.save(commit=False)
            self.object.author = self.request.user

            course_id = form.cleaned_data.get('course')
            category_id = form.cleaned_data.get('category')

            print(f"Course ID from form: {course_id}, Category ID from form: {category_id}")

            if course_id:
                self.object.course = Course.objects.get(id=course_id)
                print(f"Assigned Course: {self.object.course}")

            if category_id:
                category = ExerciseCategory.objects.get(id=category_id)
                self.object.category = category
                print(f"Assigned Category: {self.object.category}")

            self.object.save()

            if questions.is_valid():
                questions.save()
                for question_formset in choices:
                    if question_formset.is_valid():
                        question_formset.save()

            # Save the form and related question and choice formsets
            form.save_m2m()
            for question_formset in choices:
                if question_formset.is_valid():
                    question_formset.save()

        return super(ExerciseUpdateView, self).form_valid(form)

    def test_func(self):
        exercise = self.get_object()
        return self.request.user == exercise.author



class ExerciseDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Exercise
    success_url = '/exercise'

    def test_func(self):
        exercise = self.get_object()
        return self.request.user == exercise.author

    def delete(self, *args, **kwargs):
        # Get the exercise object
        exercise = self.get_object()

        # Delete related user answers and attempts
        UserAnswer.objects.filter(exercise=exercise).delete()
        Attempt.objects.filter(exercise=exercise).delete()

        # Call the superclass method to delete the Exercise
        return super(ExerciseDeleteView, self).delete(*args, **kwargs)


class ExerciseSelectForm(forms.Form):
    exercise = forms.ModelChoiceField(queryset=Exercise.objects.all(), required=True, label="Select an Exercise")


class GradeListView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = 'learning_app/grade_detail.html'
    form_class = CourseSelectForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'course' in self.request.GET:
            course_id = self.request.GET.get('course')
            course = Course.objects.get(pk=course_id)
            exercises = course.exercises.all()

            exercise_grades = []
            for exercise in exercises:
                grades_data = []
                students = User.objects.filter(attempt__exercise=exercise).distinct()
                for student in students:
                    attempts = Attempt.objects.filter(
                        exercise=exercise,
                        user=student
                    ).order_by('attempt_number')

                    attempts_list = list(attempts[:3]) + [None] * (3 - attempts.count())

                    highest_score = attempts.aggregate(Max('score'))['score__max'] or 0
                    grades_data.append({
                        'student': student,
                        'attempts': attempts_list,
                        'highest_score': highest_score,
                    })
                exercise_grades.append((exercise, grades_data))

            context.update({
                'selected_course': course,
                'exercise_grades': exercise_grades,
            })
        return context

    def test_func(self):
        return self.request.user.profile.role == 'TEACHER'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs



class GradeExerciseDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Attempt
    template_name = 'learning_app/grade_exercise_detail.html'

    def test_func(self):
        attempt = self.get_object()
        return self.request.user == attempt.user or self.request.user.profile.role == 'TEACHER'

    def get_object(self, queryset=None):
        user_id = self.kwargs.get('user_id')
        exercise_id = self.kwargs.get('exercise_id')
        attempt_id = self.kwargs.get('attempt_id')
        try:
            return Attempt.objects.get(
                pk=attempt_id,
                user__id=user_id,
                exercise__id=exercise_id
            )
        except Attempt.DoesNotExist:
            raise Http404("No Attempt found matching the query.")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        attempt = self.get_object()

        user_answers = UserAnswer.objects.filter(attempt=attempt)
        questions_and_answers = []

        for question in attempt.exercise.questions.all():
            user_answer = user_answers.filter(question=question).first()
            correct_answer = question.choices.filter(is_correct=True).first()
            questions_and_answers.append({
                'question': question,
                'user_answer': user_answer.choice if user_answer else None,
                'correct_answer': correct_answer if correct_answer else None
            })

        context['questions_and_answers'] = questions_and_answers
        return context


# All of the Courses methods -------------------------------------------------------------------- Courses methods ->
class CourseListView(ListView):
    model = Course
    template_name = 'learning_app/course_list.html'
    context_object_name = 'courses'

    def get_queryset(self):
        queryset = super().get_queryset()
        self.form = CourseSearchForm(self.request.GET)
        if self.form.is_valid():
            query = self.form.cleaned_data.get('query', '')
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(code__icontains=query) |
                Q(author__username__icontains=query) |
                Q(subject__name__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.form
        return context


class CourseDetailView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = 'learning_app/course_detail.html'
    context_object_name = 'course'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.get_object()
        context['categories_with_weights'] = course.categories.all()
        return context


class CourseCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'learning_app/course_form.html'
    success_url = reverse_lazy('course-list')

    def form_valid(self, form):
        course = form.save(commit=False)
        course.author = self.request.user
        course.save()

        num_categories = form.cleaned_data['num_categories']
        for i in range(1, num_categories + 1):
            category_name = form.cleaned_data.get(f'category_name_{i}', 'Unnamed Category')
            category_weight = form.cleaned_data.get(f'category_weight_{i}', 0.0)

            category, created = ExerciseCategory.objects.get_or_create(
                name=category_name,
                defaults={'weight': category_weight}
            )
            if not created:
                category.weight = category_weight
                category.save()

            course.categories.add(category)

        return super().form_valid(form)

    def test_func(self):
        return self.request.user.profile.role == 'TEACHER'


class UpdateCourseView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Course
    form_class = CourseForm
    template_name = 'learning_app/course_form.html'
    success_url = reverse_lazy('course-list')

    def form_valid(self, form):
        total_weight = 0
        course = form.save()  # Save the course instance

        num_categories = form.cleaned_data.get('num_categories') or 0
        existing_categories = list(course.categories.all())

        # Process existing categories
        for i, category in enumerate(existing_categories, start=1):
            category_name_field = f'category_name_{i}'
            category_weight_field = f'category_weight_{i}'
            category_delete_field = f'category_delete_{i}'

            category_delete = form.cleaned_data.get(category_delete_field, False)
            category_name = form.cleaned_data.get(category_name_field, category.name)
            category_weight = form.cleaned_data.get(category_weight_field, category.weight)

            if not category_delete:
                total_weight += float(category_weight)
                category.name = category_name
                category.weight = category_weight
                category.save()
            else:
                course.categories.remove(category)  # Remove the category from the course
                category.delete()  # Delete the category

        # Process new categories
        for i in range(len(existing_categories) + 1, num_categories + 1):
            category_name = form.cleaned_data.get(f'category_name_{i}', 'Unnamed Category')
            category_weight = form.cleaned_data.get(f'category_weight_{i}', 0.0)
            total_weight += float(category_weight)

            # Create new category
            new_category, created = ExerciseCategory.objects.get_or_create(
                name=category_name,
                defaults={'weight': category_weight}
            )
            if not created:
                new_category.weight = category_weight
                new_category.save()

            course.categories.add(new_category)  # Add the new category to the course

        # Validate total weight
        if total_weight != 100:
            messages.error(self.request, "The total weight of all categories must add up to 100%.")
            return self.form_invalid(form)

        return super().form_valid(form)

    def test_func(self):
        course = self.get_object()
        return self.request.user == course.author


class CourseDeleteView(DeleteView):
    model = Course
    success_url = reverse_lazy('course-list')  # Redirect to course list after deletion
    template_name = 'learning_app/course_confirm_delete.html'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Transfer lessons, exercises, choices, user answers, and questions to 'GEN-101'
        Lesson.objects.filter(course=self.object).update(course=Course.objects.get(code='GEN-101'))
        Exercise.objects.filter(course=self.object).update(course=Course.objects.get(code='GEN-101'))
        Choice.objects.filter(question__exercise__course=self.object).update(
            question__exercise__course=Course.objects.get(code='GEN-101'))
        UserAnswer.objects.filter(exercise__course=self.object).update(
            exercise__course=Course.objects.get(code='GEN-101'))
        Question.objects.filter(exercise__course=self.object).update(
            exercise__course=Course.objects.get(code='GEN-101'))

        # Call the parent class's delete method to delete the course
        return super().delete(request, *args, **kwargs)


class CourseEnrollView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        course_code = self.kwargs.get('code')
        course = get_object_or_404(Course, code=course_code)
        course.enrolled_students.add(request.user)
        return redirect('course-detail', pk=course.pk)


class WeightAdjustmentForm(forms.Form):
    def __init__(self, *args, **kwargs):
        course_id = kwargs.pop('course_id', None)
        super().__init__(*args, **kwargs)
        if course_id:
            categories = ExerciseCategory.objects.filter(exercises__course__id=course_id).distinct()
            for category in categories:
                field_name = f'weight_{category.id}'
                self.fields[field_name] = forms.DecimalField(max_digits=4, decimal_places=2, required=False, label=category.name)


class CourseGradeView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'learning_app/course_grade.html'

    def test_func(self):
        # Check if user is a teacher of the course
        course = get_object_or_404(Course, pk=self.kwargs['pk'])
        return self.request.user.profile.role == 'TEACHER' and self.request.user == course.author

    def get(self, request, *args, **kwargs):
        course = get_object_or_404(Course, pk=self.kwargs['pk'])
        weight_form = WeightAdjustmentForm(course_id=course.id)
        category_form = ExerciseCategoryForm()  # Assuming you have this form
        context = {'weight_form': weight_form, 'category_form': category_form, 'course': course}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        course = get_object_or_404(Course, pk=self.kwargs['pk'])
        weight_form = WeightAdjustmentForm(request.POST, course_id=course.id)
        category_form = ExerciseCategoryForm(request.POST)

        # Check if the weight form is valid
        if weight_form.is_valid():
            for field_name, weight in weight_form.cleaned_data.items():
                if field_name.startswith('weight_'):
                    category_id = int(field_name.split('_')[1])
                    ExerciseCategory.objects.filter(id=category_id).update(weight=weight)
            messages.success(request, 'Weights updated successfully.')

        # Check if the category form is valid
        if category_form.is_valid():
            new_category = category_form.save(commit=False)
            new_category.save()
            messages.success(request, 'New category added successfully.')
        else:
            messages.error(request, 'Error adding new category.')

        return self.get(request, *args, **kwargs)



