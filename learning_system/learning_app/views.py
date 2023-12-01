from collections import defaultdict

from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import transaction
from django.db.models import Max, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views import View

from .models import (Post, Reply, Lesson, Exercise, Question, Choice, UserAnswer, Attempt, Course, Subject, Profile,
                     ExerciseCategory, calculate_percentile_score)
from django.contrib import messages
from .forms import (UserRegisterForm, UserUpdateForm, ProfileUpdateForm, ReplyForm, LessonForm, ExerciseForm,
                    QuestionFormSet, ChoiceFormSet, QuizForm, CourseSearchForm, CourseForm, CourseSelectForm,
                    UpdateChoiceFormSet, PostSearchForm, ExerciseCategoryForm
                    )
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .forms import PostForm
from django import forms
from django.http import HttpResponseRedirect, Http404
from django.db import models
from django.utils import timezone




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
        return self.request.user.is_superuser or self.request.user.profile.role == 'TEACHER'



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
        return self.request.user.is_superuser or self.request.user == post.author


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    success_url = '/'

    def test_func(self):
        post = self.get_object()
        return self.request.user.is_superuser or self.request.user == post.author

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
    template_name = 'learning_app/lesson_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lesson = self.get_object()
        context['course'] = lesson.course  # Add the course to the context
        return context




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
        return self.request.user.is_superuser or self.request.user.profile.role == 'TEACHER'

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
        return self.request.user.is_superuser or self.request.user == lesson.author


class LessonDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Lesson
    success_url = '/lesson'

    def test_func(self):
        lesson = self.get_object()
        return self.request.user.is_superuser or self.request.user == lesson.author

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

    def post(self, request, *args, **kwargs):
        # Create a default exercise
        general_course = Course.objects.get_or_create(code='GEN-101', defaults={'title': 'Deleted Courses'})[0]
        deleted_exercises_category = ExerciseCategory.objects.get_or_create(name='Deleted Exercises')[0]

        exercise = Exercise.objects.create(
            title='Title',
            content='Test exercise',
            date=timezone.now(),
            author=request.user,
            course=Course.objects.get(code='GEN-101')
        )

        # Fetch the "Deleted Exercises" category
        deleted_exercises_category = ExerciseCategory.objects.get(name='Deleted Exercises')
        exercise.categories.add(deleted_exercises_category)

        # Creating 10 questions with 4 choices each
        for q_num in range(10):
            question = Question.objects.create(
                question_text=f'Question {q_num + 1}',
                exercise=exercise
            )

            for c_num in range(4):
                is_correct = True if c_num == 0 else False
                Choice.objects.create(
                    choice_text=f'Choice {c_num + 1}',
                    question=question,
                    is_correct=is_correct
                )

        # Redirect to the exercise detail page or another appropriate page
        return redirect('exercise-detail', pk=exercise.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # your existing context modifications
        return context




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


class ExerciseCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
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
        questions_formset = context['questions']
        choices_formsets = context['choices']

        if questions_formset.is_valid():
            with transaction.atomic():
                self.object = exercise
                exercise.save()

                for question_form, choice_formset in zip(questions_formset, choices_formsets):
                    if question_form.is_valid() and choice_formset.is_valid():
                        question_instance = question_form.save(commit=False)
                        question_instance.exercise = exercise
                        question_instance.save()

                        for choice_form in choice_formset:
                            choice_instance = choice_form.save(commit=False)
                            choice_instance.question = question_instance
                            choice_instance.save()

        return super(ExerciseCreateView, self).form_valid(form)

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.profile.role == 'TEACHER'



class ExerciseUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Exercise
    form_class = ExerciseForm
    template_name = 'learning_app/exercise_form.html'
    success_url = reverse_lazy('exercise')

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
        exercise = form.save(commit=False)
        exercise.author = self.request.user

        course_category = self.request.POST.get('course_category')
        if course_category:
            course_id, category_id = map(int, course_category.split('_'))
            course = Course.objects.get(id=course_id)
            category = ExerciseCategory.objects.get(id=category_id)
            exercise.course = course
            exercise.categories.clear()  # Clear existing categories
            exercise.categories.add(category)

        context = self.get_context_data()
        questions_formset = context['questions']
        choices_formsets = context['choices']

        if questions_formset.is_valid():
            with transaction.atomic():
                exercise.save()

                for question_form, choice_formset in zip(questions_formset, choices_formsets):
                    if question_form.is_valid() and choice_formset.is_valid():
                        question_instance = question_form.save(commit=False)
                        question_instance.exercise = exercise
                        question_instance.save()

                        for choice_form in choice_formset:
                            choice_instance = choice_form.save(commit=False)
                            choice_instance.question = question_instance
                            choice_instance.save()

        return super(ExerciseUpdateView, self).form_valid(form)

    def test_func(self):
        exercise = self.get_object()
        return self.request.user.is_superuser or self.request.user == exercise.author



class ExerciseDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Exercise
    success_url = '/exercise'

    def test_func(self):
        exercise = self.get_object()
        return self.request.user.is_superuser or self.request.user == exercise.author

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
            letter_grade_distribution = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
            student_weighted_grades = []

            for exercise in exercises:
                grades_data = []
                students = User.objects.filter(attempt__exercise=exercise).distinct()

                for student in students:
                    attempts = Attempt.objects.filter(exercise=exercise, user=student).order_by('attempt_number')
                    highest_score = attempts.aggregate(Max('score'))['score__max'] or 0

                    weighted_grade = course.calculate_weighted_grade_for_user(student)
                    student_weighted_grades.append((student.username, weighted_grade))
                    letter_grade = course.calculate_letter_grade(weighted_grade)
                    letter_grade_distribution[letter_grade] += 1

                    grades_data.append({
                        'student': student,
                        'attempts': list(attempts[:3]) + [None] * (3 - attempts.count()),
                        'highest_score': highest_score,
                        'weighted_grade': weighted_grade,
                    })

                exercise_grades.append((exercise, grades_data))

            highest_weighted_score = max(student_weighted_grades, key=lambda x: x[1], default=(None, 0))[1]
            lowest_weighted_score = min(student_weighted_grades, key=lambda x: x[1], default=(None, 0))[1]
            average_weighted_score = round(sum(wg[1] for wg in student_weighted_grades) / len(student_weighted_grades), 2) if student_weighted_grades else 0

            context.update({
                'selected_course': course,
                'exercise_grades': exercise_grades,
                'letter_grade_distribution': letter_grade_distribution,
                'highest_weighted_score': highest_weighted_score,
                'lowest_weighted_score': lowest_weighted_score,
                'average_weighted_score': average_weighted_score,
                'student_weighted_grades': student_weighted_grades,
            })

        return context

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.profile.role == 'TEACHER'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class GradeExerciseDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Attempt
    template_name = 'learning_app/grade_exercise_detail.html'

    def test_func(self):
        attempt = self.get_object()
        is_teacher = self.request.user.profile.role == 'TEACHER'
        is_author_of_attempt = self.request.user == attempt.user
        return self.request.user.is_superuser or is_teacher or is_author_of_attempt

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


class CourseGradesView(TemplateView):
    template_name = 'learning_app/course_grades.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        subjects = Subject.objects.all()
        subject_grade_data = {}

        for subject in subjects:
            # Initialize grade distribution for the subject
            subject_grades = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}

            # Get all courses for this subject
            courses = Course.objects.filter(subject=subject)

            for course in courses:
                # Get all weighted grades for students in the course
                all_weighted_grades = course.get_all_weighted_grades()

                # Convert weighted grades to letter grades and accumulate
                for weighted_grade in all_weighted_grades:
                    letter_grade = course.calculate_letter_grade(weighted_grade)
                    if letter_grade in subject_grades:
                        subject_grades[letter_grade] += 1

            subject_grade_data[subject.name] = subject_grades

        context['subjects'] = subjects
        context['subject_grade_data'] = subject_grade_data
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
        user = self.request.user

        # Gather categories and their exercises
        categories_with_exercises = []
        for category in course.categories.all():
            exercises = Exercise.objects.filter(course=course, categories=category)
            exercises_info = []
            for exercise in exercises:
                attempts = Attempt.objects.filter(exercise=exercise, user=user)
                highest_score = attempts.aggregate(Max('score'))['score__max']
                exercises_info.append({
                    'exercise': exercise,
                    'highest_score': highest_score if highest_score is not None else "N/A"
                })
            categories_with_exercises.append({
                'category': category,
                'exercises_info': exercises_info,
            })

        # Calculate the weighted grade for the user
        weighted_grade = course.calculate_weighted_grade_for_user(user)

        # Determine the letter grade
        letter_grade = course.calculate_letter_grade(weighted_grade)

        # Retrieve all weighted grades for the course
        all_weighted_grades = course.get_all_weighted_grades()

        # Calculate percentile score for the current user
        user_percentile = calculate_percentile_score(weighted_grade, all_weighted_grades)

        # Add data to context
        context.update({
            'categories_with_exercises': categories_with_exercises,
            'weighted_grade': weighted_grade,
            'letter_grade': letter_grade,
            'percentile_score': user_percentile,
            'a_grade_min': course.a_grade_min,
            'b_grade_min': course.b_grade_min,
            'c_grade_min': course.c_grade_min,
            'd_grade_min': course.d_grade_min,
            'lessons': Lesson.objects.filter(course=course)
        })

        return context




class CourseCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'learning_app/course_form.html'
    success_url = reverse_lazy('course-list')

    def form_valid(self, form):
        course = form.save(commit=False)
        course.author = self.request.user
        course.a_grade_min = form.cleaned_data['a_grade_min']
        course.b_grade_min = form.cleaned_data['b_grade_min']
        course.c_grade_min = form.cleaned_data['c_grade_min']
        course.d_grade_min = form.cleaned_data['d_grade_min']
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
        return self.request.user.is_superuser or self.request.user.profile.role == 'TEACHER'


class UpdateCourseView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Course
    form_class = CourseForm
    template_name = 'learning_app/course_form.html'
    success_url = reverse_lazy('course-list')

    def form_valid(self, form):
        course = form.save(commit=False)
        course.author = self.request.user
        course.a_grade_min = form.cleaned_data['a_grade_min']
        course.b_grade_min = form.cleaned_data['b_grade_min']
        course.c_grade_min = form.cleaned_data['c_grade_min']
        course.d_grade_min = form.cleaned_data['d_grade_min']
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
        return self.request.user.is_superuser or self.request.user == course.author


class CourseDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Course
    success_url = reverse_lazy('course-list')  # Redirect to course list after deletion
    template_name = 'learning_app/course_confirm_delete.html'

    def delete(self, *args, **kwargs):
        self.object = self.get_object()
        return super().delete(*args, **kwargs)

    def test_func(self):
        course = self.get_object()
        return self.request.user.is_superuser or self.request.user == course.author



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



