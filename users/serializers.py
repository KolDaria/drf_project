from django.contrib.auth import get_user_model
from rest_framework import serializers

from users.models import Payments

User = get_user_model()

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'avatar', 'phone', 'country')


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'phone', 'country', 'avatar', 'is_blocked')
        extra_kwargs = {'password': {'write_only': True, 'required': True}}

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class PaymentsSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    paid_course_name = serializers.CharField(source='paid_course.name', read_only=True, default=None)
    paid_lesson_name = serializers.CharField(source='paid_lesson.name', read_only=True, default=None)

    class Meta:
        model = Payments
        fields = ['id', 'user', 'user_email', 'payment_date', 'paid_course', 'paid_course_name', 'paid_lesson',
                  'paid_lesson_name', 'payment_amount', 'payment_method']
