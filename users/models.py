from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True, verbose_name="Email")
    phone = models.CharField(
        max_length=15, blank=True, null=True, verbose_name="Телефон", help_text="Введите номер телефона"
    )
    country = models.CharField(max_length=50, blank=True, null=True, verbose_name="Страна", help_text="Укажите страну")
    avatar = models.ImageField(
        upload_to="users/avatars/", verbose_name="Аватар", blank=True, null=True, help_text="Загрузите свой аватар"
    )

    token = models.CharField(max_length=100, verbose_name="Token", blank=True, null=True)
    is_blocked = models.BooleanField(default=False, verbose_name="Заблокирован")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
