import base64

from django.core.files.base import ContentFile
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password])

    class Meta:
        model = CustomUser
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password')

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password']
        )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField()

    class Meta:
        model = CustomUser
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar')

    def get_is_subscribed(self, obj):
        """Определяем, подписан ли текущий пользователь на этого"""
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return obj.followers.filter(user=user).exists()  # Проверяем подписку


class UserListSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField()

    class Meta:
        model = CustomUser
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar')

    def get_is_subscribed(self, obj):
        """Определяем, подписан ли текущий пользователь на этого"""
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return obj.followers.filter(author=user).exists()


class AvatarSerializer(serializers.ModelSerializer):
    avatar = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['avatar']

    def validate_avatar(self, value):
        """Декодируем base64 и создаем файл изображения."""
        try:
            format, img_str = value.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(
                base64.b64decode(img_str),
                name=f"user_avatar.{ext}")
        except Exception:
            raise serializers.ValidationError(
                "Некорректный формат изображения")
        return data

    def update(self, instance, validated_data):
        """Обновляем аватар пользователя"""
        instance.avatar = validated_data["avatar"]
        instance.save()
        return instance
