"""ViewSet'ы и вьюхи API. Роутинг собирается автоматически в urls.py через DefaultRouter."""
from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.request import Request
from rest_framework.response import Response

from .filters import BookFilter
from .models import Book, Tag, UserBook
from .serializers import BookSerializer, RegisterSerializer, TagSerializer, UserBookSerializer

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """Публичная регистрация нового пользователя."""

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class TagViewSet(viewsets.ModelViewSet):
    """Теги для книг. Читать может любой, создавать/менять — только авторизованные."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class BookViewSet(viewsets.ModelViewSet):
    """
    Общий каталог книг — читать может любой, добавлять/менять
    только авторизованные пользователи.
    """

    queryset = Book.objects.all().prefetch_related("tags")
    serializer_class = BookSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = BookFilter
    search_fields = ["title", "author"]


class UserBookViewSet(viewsets.ModelViewSet):
    """
    Личная библиотека текущего пользователя: статусы, оценки, заметки.
    Каждый видит и редактирует только свои записи.
    """

    serializer_class = UserBookSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status"]

    def get_queryset(self) -> QuerySet[UserBook]:
        """Только записи текущего пользователя, с предзагрузкой связанных книг и тегов."""
        return (
            UserBook.objects.filter(user=self.request.user)
            .select_related("book")
            .prefetch_related("book__tags")
        )

    def perform_create(self, serializer: UserBookSerializer) -> None:
        """
        Создаёт запись для текущего пользователя.

        Явно проверяем дубликат до обращения к БД: без этой проверки
        повторное добавление уже имеющейся книги падает необработанным
        IntegrityError (500) вместо аккуратного 400 — ограничение
        уникальности в модели ловит это только на уровне БД.
        """
        book = serializer.validated_data.get("book")
        if UserBook.objects.filter(user=self.request.user, book=book).exists():
            raise serializers.ValidationError(
                {"book_id": "Эта книга уже есть в твоей библиотеке."}
            )
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"])
    def stats(self, request: Request) -> Response:
        """
        Статистика чтения текущего пользователя: всего книг, разбивка
        по статусам, средняя оценка и количество оценённых книг.
        """
        queryset = self.get_queryset()

        status_counts = queryset.values("status").annotate(count=Count("id"))
        by_status = {status_value: 0 for status_value, _ in UserBook.Status.choices}
        for entry in status_counts:
            by_status[entry["status"]] = entry["count"]

        rated_books = queryset.filter(rating__isnull=False)
        avg_result = rated_books.aggregate(avg=Avg("rating"))
        average_rating = round(avg_result["avg"], 2) if avg_result["avg"] is not None else None

        return Response(
            {
                "total_books": queryset.count(),
                "by_status": by_status,
                "average_rating": average_rating,
                "rated_books_count": rated_books.count(),
            }
        )
