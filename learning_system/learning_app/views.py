from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import transaction
from django.db.models import Max, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views import View

from .models import (Post, Reply, Lesson, Exercise, Question, Choice, UserAnswer, Attempt, Course, Subject, Profile)
from django.contrib import messages
from .forms import (UserRegisterForm, UserUpdateForm, ProfileUpdateForm, ReplyForm, LessonForm, ExerciseForm,
                    QuestionFormSet, ChoiceFormSet, QuizForm, CourseSearchForm, CourseForm, CourseSelectForm,
                    UpdateChoiceFormSet, PostSearchForm
                    )
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .forms import PostForm
from django import forms
from django.http import HttpResponseRedirect, Http404


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
    success_url = '/exercise/'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['questions'] = QuestionFormSet(self.request.POST)
            data['choices'] = [ChoiceFormSet(self.request.POST, prefix=str(x), queryset=Choice.objects.none()) for x in range(0, 10)]
        else:
            data['questions'] = QuestionFormSet(queryset=Question.objects.none())
            data['choices'] = [ChoiceFormSet(prefix=str(x), queryset=Choice.objects.none()) for x in range(0, 10)]
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        questions = context['questions']
        with transaction.atomic():
            form.instance.author = self.request.user
            self.object = form.save()

            if questions.is_valid():
                question_instances = questions.save(commit=False)
                for question in question_instances:
                    question.exercise = self.object
                    question.save()

                choices = context['choices']
                if all(choice_formset.is_valid() for choice_formset in choices):
                    for question, choice_formset in zip(question_instances, choices):
                        choice_instances = choice_formset.save(commit=False)
                        for choice in choice_instances:
                            choice.question = question
                            choice.save()

        return super().form_valid(form)


class ExerciseUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Exercise
    form_class = ExerciseForm
    template_name = 'learning_app/exercise_form.html'
    success_url = '/exercise/'

    def test_func(self):
        exercise = self.get_object()
        return self.request.user == exercise.author

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['questions'] = QuestionFormSet(self.request.POST,
                                                queryset=Question.objects.filter(exercise=self.object))
            data['choices'] = [
                UpdateChoiceFormSet(self.request.POST, prefix=str(x), queryset=Choice.objects.filter(question=question)) for
                x, question in enumerate(self.object.questions.all())]
        else:
            data['questions'] = QuestionFormSet(queryset=Question.objects.filter(exercise=self.object))
            data['choices'] = [UpdateChoiceFormSet(prefix=str(x), queryset=Choice.objects.filter(question=question)) for
                               x, question in enumerate(self.object.questions.all())]
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        questions = context['questions']
        choices = context['choices']

        with transaction.atomic():
            self.object = form.save()

            if questions.is_valid():
                question_instances = questions.save()

                for question_form, choice_formset in zip(question_instances, choices):
                    if choice_formset.is_valid():
                        choice_instances = choice_formset.save(commit=False)
                        for choice in choice_instances:
                            choice.question = question_form
                            choice.save()
                        choice_formset.save_m2m()

            return super().form_valid(form)


class ExerciseDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Exercise
    success_url = '/exercise'

    def test_func(self):
        lesson = self.get_object()
        if self.request.user == lesson.author:
            return True
        return False


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
        context['lessons'] = self.object.lessons.all()
        context['exercises'] = self.object.exercises.all()
        return context



class CourseCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'learning_app/course_form.html'
    success_url = reverse_lazy('course-list')

    def form_valid(self, form):
        if not form.cleaned_data.get('subject'):
            form.instance.subject = Subject.get_default_subject()
        form.instance.author = self.request.user
        return super().form_valid(form)

    def test_func(self):
        return self.request.user.profile.role == 'TEACHER'


class CourseEnrollView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        course_code = self.kwargs.get('code')
        course = get_object_or_404(Course, code=course_code)
        course.enrolled_students.add(request.user)
        return redirect('course-detail', pk=course.pk)



