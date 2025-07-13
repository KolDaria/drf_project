from django.urls import path

from users.apps import UsersConfig
from users.views import UserCreate, PaymentListAPIView

app_name = UsersConfig.name


urlpatterns = [
    path('users/',UserCreate.as_view(), name='user-create'),
    path('payments/',PaymentListAPIView.as_view(), name='payment-list'),
]
