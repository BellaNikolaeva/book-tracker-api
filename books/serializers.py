"""Сериализаторы: превращение моделей books в JSON и обратно, включая кастомную валидацию."""
from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from rest_framework import serializers

from .models import Book, Tag, UserBook

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    """Тег книги."""

    class Meta:
        model = Tag
        fields = ["id", "name"]


class BookSerializer(serializers.ModelSerializer):
    """
    Книга общего каталога.

    `tags` — только для чтения (список объектов при GET), `tag_ids` — только
    для записи (список id при POST/PATCH). Разделение нужно, чтобы не путать
    клиента: он либо получает вложенные теги, либо отправляет их id.
    """

    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), source="tags", many=True, write_only=True, required=False
    )

    class Meta:
        model = Book
        fields = [
            "id", "title", "author", "genre", "year_published",
            "cover_url", "tags", "tag_ids", "created_at",
        ]


class UserBookSerializer(serializers.ModelSerializer):
    """Запись личной библиотеки: статус чтения, оценка, заметки конкретного пользователя."""

    book = BookSerializer(read_only=True)
    book_id = serializers.PrimaryKeyRelatedField(
        queryset=Book.objects.all(), source="book", write_only=True
    )

    class Meta:
        model = UserBook
        fields = [
            "id", "book", "book_id", "status", "rating",
            "notes", "started_at", "finished_at", "updated_at",
        ]

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Оценку можно поставить только книге со статусом `finished`."""
        status = attrs.get("status", getattr(self.instance, "status", None))
        rating = attrs.get("rating", getattr(self.instance, "rating", None))
        if rating and status != UserBook.Status.FINISHED:
            raise serializers.ValidationError(
                "Оценку можно поставить только прочитанной книге."
            )
        return attrs


class RegisterSerializer(serializers.ModelSerializer):
    """Регистрация нового пользователя. Пароль только для записи, хешируется через create_user."""

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]

    def create(self, validated_data: dict[str, Any]) -> AbstractUser:
        return User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
        )
