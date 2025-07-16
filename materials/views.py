from rest_framework import generics, permissions, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from materials.models import Course, Lesson
from materials.permissions import IsModerator, IsOwner
from materials.serializers import CourseSerializer, LessonSerializer


class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer

    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.groups.filter(name='Модераторы').exists():
            return Course.objects.prefetch_related('lessons')
        return Course.objects.filter(owner=self.request.user).prefetch_related('lessons')

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_permissions(self):
        if self.action == 'create' or self.action == 'destroy':
            permission_classes = [IsAuthenticated, IsAdminUser]
        elif self.action in ['update', 'partial_update', 'retrieve']:
            permission_classes = [IsAuthenticated, IsOwner, IsModerator]
        elif self.action == 'list':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_update(self, serializer):
        if self.request.user != self.get_object().owner and not self.request.user.groups.filter(
                name='Модераторы').exists():
            raise PermissionDenied("У вас нет разрешения на обновление этого курса.")
        serializer.save()

    def perform_destroy(self, instance):
        if self.request.user != instance.owner and not self.request.user.is_staff:
            raise PermissionDenied("У вас нет разрешения на удаление этого курса.")
        instance.delete()


class LessonCreateAPIView(generics.CreateAPIView):
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(IsOwner=self.request.user)


class LessonListAPIView(generics.ListAPIView):
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated, IsOwner, IsAdminUser]
