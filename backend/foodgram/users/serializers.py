import base64
import re

from django.contrib.auth.hashers import check_password
from django.core.files.base import ContentFile
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser

USERNAME_REGEX = r'^[\w.@+-]+\Z'


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )

    class Meta:
        model = CustomUser
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password')

    def validate_username(self, value):
        """Проверяем username по регулярному выражению"""
        if not re.match(USERNAME_REGEX, value):
            raise serializers.ValidationError(
                "Некорректный username. Разрешены только буквы, цифры и символы . @ + - _"
            )
        return value

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
    avatar = serializers.SerializerMethodField()  # Делаем кастомное поле

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

    def get_avatar(self, obj):
        """Возвращаем относительный путь к файлу аватара"""
        if obj.avatar:
            # Вернёт относительный путь, например "/media/users/avatars/user_avatar.png"
            return obj.avatar.url
        return None


class UserListSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()  # Используем кастомное поле

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

    def get_avatar(self, obj):
        """Возвращаем относительный путь к файлу аватара"""
        if obj.avatar:
            return obj.avatar.url  # Django сам отдаст относительный путь
        return None


class AvatarSerializer(serializers.ModelSerializer):
    avatar = serializers.CharField(
        write_only=True,
        required=True)  # Гарантируем, что поле требуется

    class Meta:
        model = CustomUser
        fields = ['avatar']

    def validate_avatar(self, value):
        """Декодируем base64 и создаем файл изображения."""
        if not value:
            raise serializers.ValidationError("Поле 'avatar' обязательно.")

        try:
            format, img_str = value.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(
                base64.b64decode(img_str),
                name=f"user_avatar.{ext}"
            )
        except Exception:
            raise serializers.ValidationError(
                "Некорректный формат изображения.")

        return data

    def update(self, instance, validated_data):
        """Обновляем аватар пользователя"""
        avatar = validated_data.get(
            "avatar")  # Используем get() вместо прямого доступа

        if avatar is None:
            raise serializers.ValidationError(
                {"avatar": "Поле 'avatar' обязательно."})

        instance.avatar = avatar
        instance.save()
        return instance
