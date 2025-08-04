from datetime import timezone

from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from materials.models import Course, Lesson
from materials.paginators import VehiclePaginator
from materials.permissions import IsModerator, IsOwner
from materials.serializers import CourseSerializer, LessonSerializer
from materials.services import StripeApiService
from materials.tasks import send_course_update_notification
from users.models import Payments, Subscription

stripe_service = StripeApiService()


class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    pagination_class = VehiclePaginator

    def get_queryset(self):

        if self.request.user.is_staff or self.request.user.groups.filter(name='Модераторы').exists():
            return Course.objects.all().prefetch_related('lessons')

        if self.action == 'list':
            return Course.objects.filter(owner=self.request.user).prefetch_related('lessons')

        return Course.objects.all().prefetch_related('lessons')

    def create(self, request, *args, **kwargs):
        """Переопределяем метод create, чтобы добавить проверку прав доступа."""
        if not self.request.user.is_staff and not self.request.user.groups.filter(name='Модераторы').exists():
            raise PermissionDenied("У вас нет прав на создание курса.")
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_permissions(self):
        if self.action in ['update', 'partial_update',
                           'retrieve']:
            permission_classes = [IsAuthenticated, IsOwner]
        elif self.action in ['create', 'list', 'destroy']:
            if self.action == 'list':
                permission_classes = [IsAuthenticated]
            elif self.action == 'destroy':
                permission_classes = [IsAuthenticated]
            else:
                permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_destroy(self, instance):
        if self.request.user != instance.owner:
            raise PermissionDenied("У вас нет разрешения на удаление этого курса.")
        instance.delete()

    @action(detail=True, methods=['post'])
    def subscribe(self, request, pk=None):
        course = self.get_object()
        user = request.user

        if Subscription.objects.filter(user=user, course=course).exists():
            return Response({"message": "Вы уже подписаны на этот курс."}, status=status.HTTP_400_BAD_REQUEST)

        Subscription.objects.create(user=user, course=course)

        serializer = self.get_serializer(course)
        return Response({"message": "Вы успешно подписались на этот курс.", "course": serializer.data},
                        status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def unsubscribe(self, request, pk=None):
        course = self.get_object()
        user = request.user

        try:
            subscription = Subscription.objects.get(user=user, course=course)
            subscription.delete()

            serializer = self.get_serializer(course)
            return Response({"message": "Вы успешно отписались от этого курса.", "course": serializer.data},
                            status=status.HTTP_200_OK)

        except Subscription.DoesNotExist:
            return Response({"message": "Вы не подписаны на этот курс."}, status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, context={'request': request})
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """
        Переопределяем метод update для отправки уведомлений подписчикам.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Отправка уведомлений подписчикам
        subscriptions = Subscription.objects.filter(course=instance)
        for subscription in subscriptions:
            if subscription.user.email:
                try:
                    send_course_update_notification.delay(
                        course_name=instance.name,
                        course_id=instance.pk,
                        recipient_email=subscription.user.email,
                    )
                except Exception as e:
                    print(
                        f"Ошибка при отправке уведомления подписчику {subscription.user.email}: {e}")  # Логируем ошибки

        return Response(serializer.data)


class LessonCreateAPIView(generics.CreateAPIView):
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class LessonListAPIView(generics.ListAPIView):
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = VehiclePaginator

    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.groups.filter(name='Модераторы').exists():
            return Lesson.objects.select_related('course')
        return Lesson.objects.filter(owner=self.request.user).select_related('course')


class LessonRetrieveAPIView(generics.RetrieveAPIView):
    serializer_class = LessonSerializer
    queryset = Lesson.objects.all()
    permission_classes = [IsAuthenticated, IsOwner, IsModerator]


class LessonUpdateAPIView(generics.UpdateAPIView):
    serializer_class = LessonSerializer
    queryset = Lesson.objects.all()
    permission_classes = [IsAuthenticated, IsOwner, IsModerator]


class LessonDestroyAPIView(generics.DestroyAPIView):
    queryset = Lesson.objects.all()
    permission_classes = [IsAuthenticated, (IsOwner | IsAdminUser | IsModerator)]


class CreateStripeCheckoutSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, course_id):
        """
        Создает сессию Stripe Checkout для оплаты курса.
        """
        course = get_object_or_404(Course, pk=course_id)

        # 1. Получаем или создаем Price ID в Stripe
        stripe_price_id = stripe_service.get_create_stripe_price(course)
        if not stripe_price_id:
            return Response(
                {"error": "Не удалось создать или получить Stripe Price ID."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # 2.  Формируем URL-ы для успеха и отмены платежа.
        success_url = request.build_absolute_uri(reverse('materials:payment_success', args=[course.pk]))  # materials: из urls.py
        cancel_url = request.build_absolute_uri(reverse('materials:payment_cancel', args=[course.pk]))

        # 3. Создаем сессию Stripe Checkout
        session = stripe_service.create_stripe_checkout_session(
            price_id=stripe_price_id,
            success_url=success_url,
            cancel_url=cancel_url
        )

        if not session:
            return Response(
                {"error": "Не удалось создать сессию Stripe Checkout."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # 4. Создаем запись о платеже в нашей системе (используем модель Payments из users)
        from users.models import Payments  # Импортируем модель Payments

        payment = Payments.objects.create(
            user=request.user,
            paid_course=course,
            payment_date=timezone.now(),
            payment_amount=course.price,
            payment_method='stripe',  # Или константа
            stripe_session_id=session.id,
            payment_link=session.url,
        )

        # 5. Возвращаем URL для перенаправления пользователя на Stripe
        return Response({"payment_url": session.url}, status=status.HTTP_200_OK)


class PaymentSuccessView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        """
        Обрабатывает успешную оплату курса.
        """
        course = get_object_or_404(Course, pk=course_id)
        # Дополнительная логика, например, предоставление доступа к курсу

        return Response({"message": "Оплата успешно произведена! Доступ к курсу предоставлен."},
                        status=status.HTTP_200_OK)


class PaymentCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        """
        Обрабатывает отмену оплаты курса.
        """
        course = get_object_or_404(Course, pk=course_id)
        # Логика при отмене платежа

        return Response({"message": "Оплата отменена."}, status=status.HTTP_200_OK)
