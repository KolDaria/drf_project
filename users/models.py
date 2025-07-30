from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models

from materials.models import Course, Lesson


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email обязателен')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        return self.create_user(email, password, **extra_fields)


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
    last_login = models.DateTimeField(auto_now=True, verbose_name="Дата последнего входа")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


class Payments(models.Model):
    PYMENT_METHOD_CHOICES = (
        ('cash', 'Наличные'),
        ('transfer', 'Перевод на счет'),
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        help_text="Выберите пользователя",
        related_name="payments"
    )
    payment_date = models.DateTimeField(
        verbose_name="Дата оплаты",
        help_text="Укажите дату совершения платежа"
    )
    paid_course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        verbose_name="Оплаченный курс",
        help_text="Выберите оплаченный курс",
        related_name="payments",
        blank=True,
        null=True
    )
    paid_lesson = models.ForeignKey(
        Lesson,
        on_delete=models.SET_NULL,
        verbose_name="Оплаченный урок",
        help_text="Выберите оплаченный урок",
        related_name="payments",
        blank=True,
        null=True
    )
    payment_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Сумма оплаты",
        help_text="Укажите сумму оплаты"
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PYMENT_METHOD_CHOICES,
        verbose_name="Способ оплаты",
        help_text="Выберите способ оплаты"
    )
    stripe_session_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Stripe сесии ID"
    )
    payment_link = models.URLField(
        blank=True,
        null=True,
        verbose_name="Ссылка на оплату"
    )
    payment_status = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Статус платежа"
    )

    def __str__(self):
        return f"Платеж от {self.user} на сумму {self.payment_amount}"

    class Meta:
        verbose_name = "Платеж"
        verbose_name_plural = "Платежи"


class Subscription(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    subscribed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - {self.course.name}"

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        unique_together = ('user', 'course')
