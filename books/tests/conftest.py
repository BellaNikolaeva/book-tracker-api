"""
Общие фикстуры для всего тестового пакета books/tests/.

pytest автоматически подхватывает conftest.py из этой папки и делает
все фикстуры отсюда доступными в любом test_*.py рядом — без импортов.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from books.models import Book, Tag

User = get_user_model()


# --- пользователи и авторизованные клиенты ---

@pytest.fixture
def user(db):
    """Основной тестовый пользователь."""
    return User.objects.create_user(username="bella", password="testpass123")


@pytest.fixture
def other_user(db):
    """Второй пользователь — для тестов на изоляцию данных между аккаунтами."""
    return User.objects.create_user(username="another_user", password="testpass123")


@pytest.fixture
def auth_client(user):
    """API-клиент, уже авторизованный как `user`."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def other_auth_client(other_user):
    """API-клиент, авторизованный как `other_user` — не путать с `auth_client`."""
    client = APIClient()
    client.force_authenticate(user=other_user)
    return client


# --- общие объекты предметной области ---

@pytest.fixture
def book(db):
    """Одна книга без тегов — базовый вариант для большинства тестов."""
    return Book.objects.create(
        title="Страж порядка", author="Неизвестный автор", genre="drama", year_published=2018
    )


@pytest.fixture
def other_book(db):
    """Вторая книга — нужна там, где важно различать записи (фильтры, my-books)."""
    return Book.objects.create(
        title="Мастер и Маргарита", author="Михаил Булгаков", genre="fantasy", year_published=1967
    )


@pytest.fixture
def tagged_book(db):
    """Книга с тегом — для тестов фильтрации по тегу и по году."""
    tagged = Book.objects.create(
        title="Дюна", author="Фрэнк Герберт", genre="sci-fi", year_published=1965
    )
    tag = Tag.objects.create(name="классика")
    tagged.tags.add(tag)
    return tagged


@pytest.fixture
def tag(db):
    """Один тег без привязки к книге."""
    return Tag.objects.create(name="классика")
