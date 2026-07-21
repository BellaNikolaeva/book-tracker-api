"""Фильтрация каталога книг по жанру, тегу и диапазону года издания."""
import django_filters as filters

from .models import Book


class BookFilter(filters.FilterSet):
    """
    Поддерживаемые query-параметры для /api/books/:
    ?genre=drama&tag=классика&year_from=2000&year_to=2020
    """

    genre = filters.CharFilter(field_name="genre", lookup_expr="iexact")
    tag = filters.CharFilter(field_name="tags__name", lookup_expr="iexact")
    year_from = filters.NumberFilter(field_name="year_published", lookup_expr="gte")
    year_to = filters.NumberFilter(field_name="year_published", lookup_expr="lte")

    class Meta:
        model = Book
        fields = ["genre", "tag", "year_from", "year_to"]
