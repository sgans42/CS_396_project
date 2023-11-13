from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from PIL import Image
from django.urls import reverse

# Create your models here.


class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    @classmethod
    def get_default_subject(cls):
        general, created = cls.objects.get_or_create(name='General')
        return general


class Course(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='courses')
    code = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=100)
    description = models.TextField()
    enrolled_students = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='enrolled_courses', blank=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='taught_courses'
    )

    def __str__(self):
        return f"{self.title} ({self.code})"



class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='default.png', upload_to='profile_pics')
    ROLE_CHOICES = [
        ('TEACHER', 'Teacher'),
        ('STUDENT', 'Student'), 
        ('ADMIN', 'Admin')
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='STUDENT')

    def __str__(self):
        return f'{self.user.username} Profile'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        img = Image.open(self.image.path)

        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.image.path)


class Post(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    date = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_file = models.FileField(upload_to='documents/', null=True, blank=True)
    post_visits = models.IntegerField(default=0)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post-detail', kwargs={'pk': self.pk})


class Reply(models.Model):
    post = models.ForeignKey(Post, related_name='replies', on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'Reply by {self.author.username} on {self.post.title}'


class Lesson(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    date = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    post_visits = models.IntegerField(default=0)
    document = models.FileField(upload_to='documents/', null=True, blank=True)
    video = models.URLField(max_length=200, null=True, blank=True)
    animation = models.FileField(upload_to='animations/', null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons', default=4)


    def __str__(self):
        return self.title


class Exercise(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    date = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='exercises', default=4)

    def __str__(self):
        return self.title


class Question(models.Model):
    MULTIPLE_CHOICE = 'MC'

    QUESTION_TYPES = [
        (MULTIPLE_CHOICE, 'Multiple choice'),
    ]

    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=4, choices=QUESTION_TYPES, default=MULTIPLE_CHOICE)
    subject = models.CharField(max_length=100, default="")

    def __str__(self):
        return self.question_text


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    choice_text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)  # new field to indicate the correct answer

    def __str__(self):
        return self.choice_text


class Attempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)  # date of the attempt
    score = models.IntegerField()
    attempt_number = models.IntegerField(default=0)


    def save(self, *args, **kwargs):
        # Check if this is a new attempt by looking for a primary key (id)
        if not self.pk:
            # Count the number of attempts for this user and exercise
            num_attempts = Attempt.objects.filter(user=self.user, exercise=self.exercise).count()
            if num_attempts >= 3:
                # If the user already has three attempts, raise a ValidationError
                raise ValidationError('You can only have a maximum of three attempts per exercise.')
            # If there are fewer than three attempts, set the attempt_number
            self.attempt_number = num_attempts + 1
        super(Attempt, self).save(*args, **kwargs)

    def __str__(self):
        return f'{self.user.username} - {self.exercise.title} - Attempt {self.attempt_number} - Score: {self.score}'


class UserAnswer(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)  # new field
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE)
    is_correct = models.BooleanField(default=False)
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE)  # Add this field


    def __str__(self):
        return f"{self.user.username} - {self.exercise.title} - {self.question.question_text} - {self.choice.choice_text}"
