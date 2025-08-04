from django.urls import path
from rest_framework.routers import DefaultRouter

from materials.apps import MaterialsConfig
from materials.views import (CourseViewSet, CreateStripeCheckoutSessionView, LessonCreateAPIView, LessonDestroyAPIView,
                             LessonListAPIView, LessonRetrieveAPIView, LessonUpdateAPIView, PaymentCancelView,
                             PaymentSuccessView)

app_name = MaterialsConfig.name

router = DefaultRouter()
router.register(r'course', CourseViewSet, basename='course')

urlpatterns = [
    path('lesson/create/', LessonCreateAPIView.as_view(), name='lesson_create'),
    path('lesson/', LessonListAPIView.as_view(), name='lesson_list'),
    path('lesson/<int:pk>/', LessonRetrieveAPIView.as_view(), name='lesson_get'),
    path('lesson/update/<int:pk>/', LessonUpdateAPIView.as_view(), name='lesson_update'),
    path('lesson/delete/<int:pk>/', LessonDestroyAPIView.as_view(), name='lesson_delete'),

    # URL для создания платежа за курс
    path('course/<int:course_id>/payment/', CreateStripeCheckoutSessionView.as_view(), name='create_payment'),
    path('course/<int:course_id>/payment/success/', PaymentSuccessView.as_view(), name='payment_success'),
    path('course/<int:course_id>/payment/cancel/', PaymentCancelView.as_view(), name='payment_cancel'),

] + router.urls
