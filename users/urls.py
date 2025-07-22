from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users.apps import UsersConfig
from users.views import (PaymentListAPIView, UserCreateAPIView, UserDestroyAPIView, UserListAPIView, UserProfileView,
                         UserRetrieveAPIView, UserUpdateAPIView, UserUpdateView, SubscriptionAPIView)

app_name = UsersConfig.name


urlpatterns = [
    # Аутентификация и авторизация
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # CRUD для пользователей
    path('users/', UserListAPIView.as_view(), name='user-list'),
    path('users/<int:pk>/', UserRetrieveAPIView.as_view(), name='user-retrieve'),
    path('users/<int:pk>/edit/', UserUpdateAPIView.as_view(), name='user-update-admin'),
    path('users/<int:pk>/delete/', UserDestroyAPIView.as_view(), name='user-delete'),

    # Регистрация
    path('users/register/', UserCreateAPIView.as_view(), name='user-create'),

    # Управление собственным профилем
    path('users/profile/', UserProfileView.as_view(), name='user-profile'),
    path('users/profile/edit/', UserUpdateView.as_view(), name='user-profile-edit'),

    # Платежи
    path('payments/', PaymentListAPIView.as_view(), name='payment-list'),

    # Подписки
    path('subscriptions/', SubscriptionAPIView.as_view(), name='subscription'),
]
