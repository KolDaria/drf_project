from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from materials.models import Course
from users.models import Subscription, User


class CourseViewSetTestCase(APITestCase):
    def setUp(self):
        # Создаем пользователей с разными ролями
        self.admin_user = User.objects.create_superuser(
            email='admin@example.com', password='password123')
        self.moderator_user = User.objects.create_user(
            email='moderator@example.com', password='password123')
        self.owner_user = User.objects.create_user(
            email='owner@example.com', password='password123')
        self.regular_user = User.objects.create_user(
            email='regular@example.com', password='password123')

        # Создаем группу модераторов и добавляем модератора в эту группу
        moderators_group = Group.objects.create(name='Модераторы')
        self.moderator_user.groups.add(moderators_group)

        # Создаем тестовые курсы
        self.course1 = Course.objects.create(
            name='Курс 1', description='Описание курса 1', owner=self.owner_user)
        self.course2 = Course.objects.create(
            name='Курс 2', description='Описание курса 2', owner=self.admin_user)

        # Создаем подписку для owner_user на course1
        self.subscription = Subscription.objects.create(
            user=self.owner_user, course=self.course1)

        # URLs
        self.course_list_url = reverse('materials:course-list')
        self.course_detail_url = reverse(
            'materials:course-detail', kwargs={'pk': self.course1.pk})
        self.subscribe_url = reverse('materials:course-subscribe', kwargs={'pk': self.course1.pk})
        self.unsubscribe_url = reverse('materials:course-unsubscribe', kwargs={'pk': self.course1.pk})

        # URL для SubscriptionAPIView
        self.subscription_api_url = reverse('users:subscription')

    # Тесты для получения списка курсов (list)
    def test_course_list_authenticated(self):
        """Аутентифицированный пользователь должен видеть список курсов."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.course_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_course_list_admin(self):
        """Администратор должен видеть все курсы."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.course_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_course_list_owner(self):
        """Владелец должен видеть только свои курсы."""
        self.client.force_authenticate(user=self.owner_user)
        response = self.client.get(self.course_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Курс 1')

    # Тесты для получения деталей курса (retrieve)
    def test_course_retrieve_owner(self):
        """Владелец должен иметь возможность просматривать детали своего курса."""
        self.client.force_authenticate(user=self.owner_user)
        response = self.client.get(self.course_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Курс 1')

    def test_course_retrieve_other_user(self):
        """Пользователь не должен иметь возможность просматривать детали чужого курса."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.course_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_course_retrieve_admin(self):
        """Админ должен иметь возможность просматривать детали любого курса"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.course_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Курс 1')

    # Тесты для подписки (subscribe)
    def test_subscribe_success(self):
        """Аутентифицированный пользователь может подписаться на курс."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.post(self.subscribe_url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Subscription.objects.filter(
            user=self.regular_user, course=self.course1).count(), 1)

    def test_subscribe_already_subscribed(self):
        """Пользователь не может подписаться на курс повторно."""
        self.client.force_authenticate(user=self.owner_user)
        response = self.client.post(self.subscribe_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # Тесты для отписки (unsubscribe)
    def test_unsubscribe_success(self):
        """Аутентифицированный пользователь может отписаться от курса."""
        self.client.force_authenticate(user=self.owner_user)
        response = self.client.post(self.unsubscribe_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Subscription.objects.filter(
            user=self.owner_user, course=self.course1).count(), 0)

    def test_unsubscribe_not_subscribed(self):
        """Пользователь не может отписаться, если он не подписан."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.post(self.unsubscribe_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_course_admin(self):
        """Администратор может создать курс."""
        self.client.force_authenticate(user=self.admin_user)
        data = {'name': 'Новый курс от админа', 'description': 'Описание нового курса', 'owner': self.admin_user.pk}
        response = self.client.post(self.course_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Course.objects.get(name='Новый курс от админа').owner,
                         self.admin_user)

    def test_create_course_moderator(self):
        """Модератор может создать курс."""
        self.client.force_authenticate(user=self.moderator_user)
        data = {'name': 'Новый курс от модератора',
                'description': 'Описание нового курса от модератора',
                'owner': self.moderator_user.pk}
        url = reverse('materials:course-list')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Course.objects.count(), 3)
        self.assertEqual(Course.objects.last().owner,
                         self.moderator_user)

    def test_create_course_regular_user(self):
        """Обычный пользователь не может создать курс."""
        self.client.force_authenticate(user=self.regular_user)
        data = {'name': 'Курс от обычного пользователя',
                'description': 'Описание курса от обычного пользователя'}
        url = reverse('materials:course-list')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code,
                         status.HTTP_403_FORBIDDEN)

    def test_update_course_owner(self):
        """Владелец может обновить свой курс."""
        self.client.force_authenticate(user=self.owner_user)
        data = {'name': 'Обновленный курс',
                'description': 'Обновленное описание',
                'owner': self.owner_user.pk
                }
        url = reverse('materials:course-detail', kwargs={'pk': self.course1.pk})
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Course.objects.get(pk=self.course1.pk).name,
                         'Обновленный курс')

    def test_update_course_not_owner(self):
        """Не владелец не может обновить чужой курс."""
        self.client.force_authenticate(user=self.regular_user)
        data = {'name': 'Попытка обновить чужой курс', 'description': 'Описание'}
        url = reverse('materials:course-detail', kwargs={'pk': self.course1.pk})
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_course_owner(self):
        """Владелец может удалить свой курс."""
        self.client.force_authenticate(user=self.owner_user)
        url = reverse('materials:course-detail', kwargs={'pk': self.course1.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Course.objects.filter(pk=self.course1.pk).count(),
                         0)

    def test_delete_course_not_owner(self):
        """Не владелец не может удалить чужой курс."""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('materials:course-detail', kwargs={'pk': self.course1.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_subscribe_invalid_course_id(self):
        """Тест подписки с неверным course_id."""
        self.client.force_authenticate(user=self.regular_user)
        data = {'course_id': 999}
        response = self.client.post(self.subscription_api_url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_authentication_required(self):
        """Тест, что требуется аутентификация."""
        self.client.logout()
        data = {'course_id': self.course1.pk}
        response = self.client.post(self.subscription_api_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
