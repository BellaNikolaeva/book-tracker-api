"""Модели предметной области: книги общего каталога, теги, личная библиотека пользователя."""
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Tag(models.Model):
    """Тег для группировки книг (жанр, тематика и т.п.), задаётся пользователями свободно."""

    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Book(models.Model):
    """Книга общего каталога — общая для всех пользователей, не привязана к конкретному аккаунту."""

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    genre = models.CharField(max_length=100, blank=True)
    year_published = models.PositiveIntegerField(null=True, blank=True)
    cover_url = models.URLField(blank=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name="books")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["author"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} — {self.author}"


class UserBook(models.Model):
    """
    Запись личной библиотеки: связывает пользователя с книгой и хранит
    статус чтения, оценку и заметки. Одна пара (user, book) — одна запись
    (см. ограничение unique_user_book ниже).
    """

    class Status(models.TextChoices):
        WANT_TO_READ = "want_to_read", "Хочу прочитать"
        READING = "reading", "Читаю"
        FINISHED = "finished", "Прочитано"
        DROPPED = "dropped", "Бросил(а)"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_books"
    )
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="user_entries")
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.WANT_TO_READ
    )
    rating = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    notes = models.TextField(blank=True)
    started_at = models.DateField(null=True, blank=True)
    finished_at = models.DateField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "book"], name="unique_user_book")
        ]

    def __str__(self) -> str:
        return f"{self.user} — {self.book} ({self.status})"