"""Тесты на /api/books/ — общий каталог книг."""
import pytest

from books.models import Book

# --- list & retrieve (доступны анонимно) ---

@pytest.mark.django_db
def test_anonymous_can_list_books(client, book):
    """Каталог книг открыт без авторизации."""
    # Act
    response = client.get("/api/books/")

    # Assert
    assert response.status_code == 200
    assert response.data["count"] == 1


@pytest.mark.django_db
def test_anonymous_can_retrieve_book(client, book):
    """Детали конкретной книги открыты без авторизации."""
    # Act
    response = client.get(f"/api/books/{book.id}/")

    # Assert
    assert response.status_code == 200
    assert response.data["title"] == book.title


@pytest.mark.django_db
def test_retrieve_nonexistent_book_returns_404(client):
    """Запрос несуществующей книги отвечает 404, а не падает исключением."""
    # Act
    response = client.get("/api/books/99999/")

    # Assert
    assert response.status_code == 404


# --- запись доступна только авторизованным ---

@pytest.mark.django_db
def test_anonymous_cannot_create_book(client):
    """Анонимный пользователь не может добавить книгу."""
    # Act
    response = client.post("/api/books/", {"title": "X", "author": "Y"})

    # Assert
    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_authenticated_user_can_create_book(auth_client):
    """Авторизованный пользователь может добавить книгу в общий каталог."""
    # Act
    response = auth_client.post("/api/books/", {"title": "Новая книга", "author": "Автор"})

    # Assert
    assert response.status_code == 201
    assert Book.objects.count() == 1


@pytest.mark.django_db
def test_anonymous_cannot_update_book(client, book):
    """Анонимный пользователь не может изменить книгу."""
    # Act
    response = client.patch(
        f"/api/books/{book.id}/", {"title": "Взлом"}, content_type="application/json"
    )

    # Assert
    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_authenticated_user_can_update_book(auth_client, book):
    """Авторизованный пользователь может изменить книгу, изменения сохраняются в БД."""
    # Act
    response = auth_client.patch(
        f"/api/books/{book.id}/", {"title": "Обновлённое название"}, content_type="application/json"
    )

    # Assert
    assert response.status_code == 200
    book.refresh_from_db()
    assert book.title == "Обновлённое название"


@pytest.mark.django_db
def test_anonymous_cannot_delete_book(client, book):
    """Анонимный пользователь не может удалить книгу — она остаётся в БД."""
    # Act
    response = client.delete(f"/api/books/{book.id}/")

    # Assert
    assert response.status_code in (401, 403)
    assert Book.objects.filter(id=book.id).exists()


@pytest.mark.django_db
def test_authenticated_user_can_delete_book(auth_client, book):
    """Авторизованный пользователь может удалить книгу, запись реально пропадает."""
    # Act
    response = auth_client.delete(f"/api/books/{book.id}/")

    # Assert
    assert response.status_code == 204
    assert not Book.objects.filter(id=book.id).exists()


# --- поиск и фильтры ---

@pytest.mark.django_db
@pytest.mark.parametrize(
    "search_term, expected_count",
    [
        pytest.param("Страж", 1, id="matches_title"),
        pytest.param("Неизвестный", 1, id="matches_author"),
        pytest.param("Совсем другое", 0, id="no_match"),
    ],
)
def test_search_books(client, book, search_term, expected_count):
    """Поиск находит книгу по названию и по автору, не находит нерелевантные запросы."""
    # Act
    response = client.get(f"/api/books/?search={search_term}")

    # Assert
    assert response.status_code == 200
    assert response.data["count"] == expected_count


@pytest.mark.django_db
def test_filter_by_genre(client, book, tagged_book):
    """Фильтр по жанру возвращает только книги этого жанра."""
    # Act
    response = client.get("/api/books/?genre=drama")

    # Assert
    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["title"] == book.title


@pytest.mark.django_db
def test_filter_by_tag(client, book, tagged_book):
    """Фильтр по тегу возвращает только книги с этим тегом."""
    # Act
    response = client.get("/api/books/?tag=классика")

    # Assert
    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["title"] == tagged_book.title


@pytest.mark.django_db
def test_filter_by_year_range(client, book, tagged_book):
    """Фильтр по диапазону года учитывает только книги внутри диапазона."""
    # Act
    response = client.get("/api/books/?year_from=2000&year_to=2020")

    # Assert
    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["title"] == book.title


# --- негативные и граничные случаи ---

@pytest.mark.django_db
@pytest.mark.parametrize(
    "payload, missing_field",
    [
        pytest.param({"author": "Автор"}, "title", id="missing_title"),
        pytest.param({"title": "Название"}, "author", id="missing_author"),
    ],
)
def test_create_book_requires_title_and_author(auth_client, payload, missing_field):
    """Создание книги без обязательного поля отклоняется с 400."""
    # Act
    response = auth_client.post("/api/books/", payload)

    # Assert
    assert response.status_code == 400
    assert missing_field in response.data


@pytest.mark.django_db
def test_create_book_rejects_negative_year(auth_client):
    """year_published — PositiveIntegerField, отрицательный год не проходит валидацию."""
    # Act
    response = auth_client.post(
        "/api/books/", {"title": "Книга", "author": "Автор", "year_published": -100}
    )

    # Assert
    assert response.status_code == 400


@pytest.mark.django_db
def test_create_book_with_nonexistent_tag_id_returns_400(auth_client):
    """Ссылка на несуществующий tag_id отклоняется, а не создаёт книгу с висячей связью."""
    # Act
    response = auth_client.post(
        "/api/books/", {"title": "Книга", "author": "Автор", "tag_ids": [99999]}
    )

    # Assert
    assert response.status_code == 400


@pytest.mark.django_db
def test_update_book_rejects_blank_title(auth_client, book):
    """PATCH с пустым title не должен затирать поле пустой строкой."""
    # Act
    response = auth_client.patch(
        f"/api/books/{book.id}/", {"title": ""}, content_type="application/json"
    )

    # Assert
    assert response.status_code == 400
    book.refresh_from_db()
    assert book.title != ""


@pytest.mark.django_db
def test_delete_nonexistent_book_returns_404(auth_client):
    """Удаление несуществующей книги отвечает 404, а не 204 или 500."""
    # Act
    response = auth_client.delete("/api/books/99999/")

    # Assert
    assert response.status_code == 404


@pytest.mark.django_db
def test_search_is_case_insensitive(client, book):
    """Поиск не должен зависеть от регистра — 'страж' находит 'Страж порядка'."""
    # Act
    response = client.get("/api/books/?search=страж")

    # Assert
    assert response.status_code == 200
    assert response.data["count"] == 1


@pytest.mark.django_db
def test_filter_by_genre_with_no_matches_returns_empty_list(client, book):
    """Фильтр по несуществующему жанру не падает, просто возвращает пустой список."""
    # Act
    response = client.get("/api/books/?genre=несуществующий-жанр")

    # Assert
    assert response.status_code == 200
    assert response.data["count"] == 0


@pytest.mark.django_db
def test_pagination_returns_second_page(client):
    """При количестве книг больше PAGE_SIZE (20) появляется вторая страница."""
    # Arrange
    Book.objects.bulk_create(
        [Book(title=f"Книга {i}", author="Автор") for i in range(25)]
    )

    # Act
    first_page = client.get("/api/books/")
    second_page = client.get("/api/books/?page=2")

    # Assert
    assert first_page.data["count"] == 25
    assert len(first_page.data["results"]) == 20
    assert second_page.status_code == 200
    assert len(second_page.data["results"]) == 5