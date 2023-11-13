from django.urls import path
from . import views

from .views import (PostListView, PostDetailView, PostCreateView, PostUpdateView, PostDeleteView,
					LessonListView, LessonDetailView, LessonCreateView, LessonUpdateView, LessonDeleteView,
					ExerciseListView, ExerciseDetailView, ExerciseCreateView, ExerciseUpdateView, ExerciseDeleteView,
					TakeExerciseDetailView, GradeListView, UserPostListView, UserLessonListView, UserExerciseListView,
					CourseListView, CourseCreateView, CourseDetailView, CourseEnrollView,
					GradeExerciseDetailView, TeacherCourseListView, StudentCourseListView
					)

urlpatterns = [
	path('', PostListView.as_view(), name='learning_app-home'),  # home page, Shows all Posts
	path('register/', views.register, name='learning_app-register'),

# Exercise ExerciseIndividualListView
	path('exercise/', ExerciseListView.as_view(), name='exercise'),  # shows all exercise
	path('exercise/<int:pk>/', ExerciseDetailView.as_view(), name='exercise-detail'),  # shows individual exercise
	path('exercise/take/<int:pk>/', TakeExerciseDetailView.as_view(), name='exercise-take'),  # shows individual exercise
	path('exercise/new/', ExerciseCreateView.as_view(), name='exercise-create'),  # make new exercise
	path('exercise/<int:pk>/update/', ExerciseUpdateView.as_view(), name='exercise-update'),  # Update exercise
	path('exercise/<int:pk>/delete/', ExerciseDeleteView.as_view(), name='exercise-delete'),  # Delete exercise

# Courses
	path('courses/', CourseListView.as_view(), name='course-list'),
	path('course/create/', CourseCreateView.as_view(), name='course-create'),
	path('course/<int:pk>/', CourseDetailView.as_view(), name='course-detail'),
	path('course/enroll/<str:code>/', CourseEnrollView.as_view(), name='course-enroll'),

# Profile methods
	path('profile/', views.profile, name='learning_app-profile'),  # edit profile
	path('profile/post/<str:username>/', UserPostListView.as_view(), name='user-posts'),  # individual users posts
	path('profile/lesson/<str:username>/', UserLessonListView.as_view(), name='user-lessons'),  # individual users lessons
	path('profile/exercise/<str:username>/', UserExerciseListView.as_view(), name='user-exercise'),  # individual users exercise
	path('teacher/courses/', TeacherCourseListView.as_view(), name='teacher-courses'),
	path('student/courses/', StudentCourseListView.as_view(), name='student-courses'),

	# Lessons
	path('lesson/', LessonListView.as_view(), name='lesson'),  # shows all lessons
	path('lesson/<int:pk>/', LessonDetailView.as_view(), name='lesson-detail'),  # shows individual Lesson
	path('lesson/new/', LessonCreateView.as_view(), name='lesson-create'),  # make new Lesson
	path('lesson/<int:pk>/update/', LessonUpdateView.as_view(), name='lesson-update'),  # Update Lesson
	path('lesson/<int:pk>/delete/', LessonDeleteView.as_view(), name='lesson-delete'),  # Delete Lesson

# Posts
	path('post/<int:pk>/', PostDetailView.as_view(), name='post-detail'),  # shows individual Posts
	path('post/new/', PostCreateView.as_view(), name='post-create'),  # Create Post
	path('post/<int:pk>/update/', PostUpdateView.as_view(), name='post-update'),  # Update Post
	path('post/<int:pk>/delete/', PostDeleteView.as_view(), name='post-delete'),  # Delete Post


# Grades
	path('grades/', GradeListView.as_view(), name='grade-detail'),
	path('grades/<int:user_id>/exercise/<int:exercise_id>/attempt/<int:attempt_id>/', GradeExerciseDetailView.as_view(),
		 name='grades-exercise-detail')
]