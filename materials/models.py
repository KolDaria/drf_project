from django.conf import settings
from django.db import models


class Course(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='courses'
    )
    name = models.CharField(
        max_length=150,
        verbose_name="Название",
        help_text="Введите название курса"
    )
    image = models.ImageField(
        upload_to="course/images/",
        verbose_name="Превью",
        blank=True,
        null=True,
        help_text="Загрузите превью"
    )
    description = models.TextField(
        verbose_name="Описание",
        blank=True,
        null=True,
        help_text="Введите описание курса",
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"


class Lesson(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lessons'
    )
    name = models.CharField(
        max_length=150,
        verbose_name="Название",
        help_text="Введите название урока"
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        verbose_name="Курс",
        help_text="Выберите курс",
        related_name="lessons"
    )
    description = models.TextField(
        verbose_name="Описание",
        blank=True,
        null=True,
        help_text="Введите описание урока",
    )
    image = models.ImageField(
        upload_to="lesson/images/",
        verbose_name="Превью",
        blank=True,
        null=True,
        help_text="Загрузите превью"
    )
    video_url = models.URLField(
        max_length=200,
        verbose_name="Видео",
        blank=True,
        null=True,
        help_text="Загрузите ссылку на видео"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Урок"
        verbose_name_plural = "Уроки"
