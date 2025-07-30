from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from config.settings import EMAIL_HOST_USER
from celery import shared_task
from django.core.mail import send_mail


@shared_task
def send_course_update_notification(course_name, course_id, recipient_email):
    send_mail(f'Обновление курса: {course_name}',f'Ура! курс {course_name} обновлен', EMAIL_HOST_USER, [recipient_email])
    print(f"Успешно отправлено уведомление на {recipient_email} об обновлении курса {course_name} (ID: {course_id})")

@shared_task
def block_inactive_users():
    User = get_user_model()
    inactive_users = User.objects.filter(last_login__lt=(timezone.now() - timedelta(days=30)), is_active=True)
    for user in inactive_users:
        user.is_active = False
        user.save()
        print(f"Заблокирован пользователь: {user.username}")
