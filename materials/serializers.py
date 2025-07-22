from rest_framework import serializers

from materials.models import Course, Lesson
from materials.validators import TitleValidator
from users.models import Subscription


class LessonSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.id')

    class Meta:
        model = Lesson
        fields = '__all__'
        validators = [
            TitleValidator(field='video_url'),
            serializers.UniqueTogetherValidator(fields=['video_url'], queryset=Lesson.objects.all())
        ]


class CourseSerializer(serializers.ModelSerializer):
    number_lessons = serializers.SerializerMethodField()
    lessons = LessonSerializer(many=True, read_only=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = '__all__'

    def get_number_lessons(self, instance):
        return instance.lessons.count()

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return Subscription.objects.filter(user=user, course=obj).exists()
        return False
