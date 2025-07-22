from rest_framework import generics, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from materials.models import Course, Lesson
from materials.paginators import VehiclePaginator
from materials.permissions import IsModerator, IsOwner
from materials.serializers import CourseSerializer, LessonSerializer
from users.models import Subscription


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
            return Response({"message": "Вы уже подписаны на этот курс."}, status=400)

        Subscription.objects.create(user=user, course=course)
        return Response({"message": "Вы успешно подписались на этот курс."}, status=201)

    @action(detail=True, methods=['post'])
    def unsubscribe(self, request, pk=None):
        course = self.get_object()
        user = request.user

        try:
            subscription = Subscription.objects.get(user=user, course=course)
            subscription.delete()
            return Response({"message": "Вы успешно отписались от этого курса."}, status=200)
        except Subscription.DoesNotExist:
            return Response({"message": "Вы не подписаны на этот курс."}, status=400)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, context={'request': request})
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
