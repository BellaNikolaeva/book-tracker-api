"""Тесты на /api/my-books/ — личная библиотека пользователя и статистика."""
import pytest

from books.models import UserBook


@pytest.fixture
def user_book(db, user, book):
    """Запись `book` уже добавлена в библиотеку `user` со статусом reading."""
    return UserBook.objects.create(user=user, book=book, status="reading")


# --- list ---

@pytest.mark.django_db
def test_anonymous_cannot_list_my_books(client):
    """Личная библиотека недоступна без авторизации."""
    # Act
    response = client.get("/api/my-books/")

    # Assert
    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_authenticated_user_lists_own_books(auth_client, user_book):
    """Авторизованный пользователь видит свои записи в списке."""
    # Act
    response = auth_client.get("/api/my-books/")

    # Assert
    assert response.status_code == 200
    assert response.data["count"] == 1


@pytest.mark.django_db
def test_user_sees_only_own_books(auth_client, other_auth_client, book):
    """Записи одного пользователя не видны в списке другого."""
    # Arrange — второй пользователь добавляет книгу себе
    other_auth_client.post("/api/my-books/", {"book_id": book.id, "status": "reading"})

    # Act
    response = auth_client.get("/api/my-books/")

    # Assert
    assert response.data["count"] == 0


@pytest.mark.django_db
def test_filter_by_status(auth_client, user, book, other_book):
    """Фильтр по статусу возвращает только записи с этим статусом."""
    # Arrange
    UserBook.objects.create(user=user, book=book, status="reading")
    UserBook.objects.create(user=user, book=other_book, status="finished")

    # Act
    response = auth_client.get("/api/my-books/?status=finished")

    # Assert
    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["book"]["title"] == other_book.title


# --- create ---

@pytest.mark.django_db
def test_anonymous_cannot_add_book(client, book):
    """Анонимный пользователь не может добавить книгу в чужую/любую библиотеку."""
    # Act
    response = client.post("/api/my-books/", {"book_id": book.id, "status": "reading"})

    # Assert
    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_authenticated_user_can_add_book(auth_client, book):
    """Авторизованный пользователь может добавить книгу в свою библиотеку."""
    # Act
    response = auth_client.post("/api/my-books/", {"book_id": book.id, "status": "reading"})

    # Assert
    assert response.status_code == 201
    assert UserBook.objects.get(book=book).status == "reading"


@pytest.mark.django_db
def test_cannot_add_same_book_twice(auth_client, user_book, book):
    """Повторное добавление уже имеющейся книги отклоняется с 400, а не падает 500."""
    # Act — `user_book` уже добавила эту книгу для того же пользователя
    response = auth_client.post("/api/my-books/", {"book_id": book.id, "status": "want_to_read"})

    # Assert
    assert response.status_code == 400


@pytest.mark.django_db
@pytest.mark.parametrize(
    "status, rating, expected_status_code",
    [
        pytest.param("reading", 5, 400, id="rating_without_finished_rejected"),
        pytest.param("finished", 5, 201, id="rating_with_finished_allowed"),
    ],
)
def test_rating_requires_finished_status(auth_client, book, status, rating, expected_status_code):
    """Оценку можно поставить только книге со статусом finished."""
    # Act
    response = auth_client.post(
        "/api/my-books/", {"book_id": book.id, "status": status, "rating": rating}
    )

    # Assert
    assert response.status_code == expected_status_code


# --- retrieve ---

@pytest.mark.django_db
def test_user_can_retrieve_own_entry(auth_client, user_book):
    """Пользователь может посмотреть свою запись."""
    # Act
    response = auth_client.get(f"/api/my-books/{user_book.id}/")

    # Assert
    assert response.status_code == 200
    assert response.data["status"] == "reading"


@pytest.mark.django_db
def test_user_cannot_retrieve_others_entry(other_auth_client, user_book):
    """Чужая запись не видна — 404, поскольку queryset уже отфильтрован по пользователю."""
    # Act
    response = other_auth_client.get(f"/api/my-books/{user_book.id}/")

    # Assert
    assert response.status_code == 404


# --- update ---

@pytest.mark.django_db
def test_user_can_update_own_entry(auth_client, user_book):
    """Пользователь может изменить статус и оценку своей записи."""
    # Act
    response = auth_client.patch(
        f"/api/my-books/{user_book.id}/",
        {"status": "finished", "rating": 4},
        content_type="application/json",
    )

    # Assert
    assert response.status_code == 200
    user_book.refresh_from_db()
    assert user_book.status == "finished"
    assert user_book.rating == 4


@pytest.mark.django_db
def test_user_cannot_update_others_entry(other_auth_client, user_book):
    """Чужую запись изменить нельзя, исходные данные не меняются."""
    # Act
    response = other_auth_client.patch(
        f"/api/my-books/{user_book.id}/", {"status": "finished"}, content_type="application/json"
    )

    # Assert
    assert response.status_code == 404
    user_book.refresh_from_db()
    assert user_book.status == "reading"


@pytest.mark.django_db
def test_update_rejects_rating_without_finished_status(auth_client, user_book):
    """Нельзя проставить рейтинг записи, которая не в статусе finished."""
    # Act — `user_book` имеет статус reading
    response = auth_client.patch(
        f"/api/my-books/{user_book.id}/", {"rating": 5}, content_type="application/json"
    )

    # Assert
    assert response.status_code == 400


# --- delete ---

@pytest.mark.django_db
def test_user_can_delete_own_entry(auth_client, user_book):
    """Пользователь может удалить свою запись, она реально пропадает из БД."""
    # Act
    response = auth_client.delete(f"/api/my-books/{user_book.id}/")

    # Assert
    assert response.status_code == 204
    assert not UserBook.objects.filter(id=user_book.id).exists()


@pytest.mark.django_db
def test_user_cannot_delete_others_entry(other_auth_client, user_book):
    """Чужую запись удалить нельзя, она остаётся в БД."""
    # Act
    response = other_auth_client.delete(f"/api/my-books/{user_book.id}/")

    # Assert
    assert response.status_code == 404
    assert UserBook.objects.filter(id=user_book.id).exists()


# --- stats ---

@pytest.mark.django_db
def test_stats_for_empty_list(auth_client):
    """У пользователя без книг статистика не падает, а возвращает нули/null."""
    # Act
    response = auth_client.get("/api/my-books/stats/")

    # Assert
    assert response.status_code == 200
    assert response.data["total_books"] == 0
    assert response.data["average_rating"] is None
    assert response.data["rated_books_count"] == 0


@pytest.mark.django_db
def test_stats_with_mixed_data(auth_client, user, book, other_book):
    """Статистика верно считает разбивку по статусам и средний рейтинг."""
    # Arrange
    UserBook.objects.create(user=user, book=book, status="finished", rating=4)
    UserBook.objects.create(user=user, book=other_book, status="reading")

    # Act
    response = auth_client.get("/api/my-books/stats/")

    # Assert
    assert response.status_code == 200
    assert response.data["total_books"] == 2
    assert response.data["by_status"]["finished"] == 1
    assert response.data["by_status"]["reading"] == 1
    assert response.data["by_status"]["want_to_read"] == 0
    assert response.data["average_rating"] == 4.0
    assert response.data["rated_books_count"] == 1


@pytest.mark.django_db
def test_stats_only_counts_own_books(auth_client, other_auth_client, book):
    """Статистика не подмешивает данные другого пользователя."""
    # Arrange
    other_auth_client.post(
        "/api/my-books/", {"book_id": book.id, "status": "finished", "rating": 5}
    )

    # Act
    response = auth_client.get("/api/my-books/stats/")

    # Assert
    assert response.data["total_books"] == 0


# --- негативные и граничные случаи ---

@pytest.mark.django_db
def test_add_book_requires_book_id(auth_client):
    """Запрос без book_id отклоняется с 400."""
    # Act
    response = auth_client.post("/api/my-books/", {"status": "reading"})

    # Assert
    assert response.status_code == 400
    assert "book_id" in response.data


@pytest.mark.django_db
def test_add_nonexistent_book_returns_400(auth_client):
    """Ссылка на несуществующий book_id отклоняется, а не создаёт запись с висячей связью."""
    # Act
    response = auth_client.post("/api/my-books/", {"book_id": 99999, "status": "reading"})

    # Assert
    assert response.status_code == 400


@pytest.mark.django_db
def test_add_book_rejects_invalid_status_value(auth_client, book):
    """Статус вне enum (Status.choices) отклоняется — нельзя записать что попало."""
    # Act
    response = auth_client.post(
        "/api/my-books/", {"book_id": book.id, "status": "не_существующий_статус"}
    )

    # Assert
    assert response.status_code == 400


@pytest.mark.django_db
@pytest.mark.parametrize("rating", [0, 6, -1], ids=["zero", "above_max", "negative"])
def test_rating_outside_valid_range_rejected(auth_client, book, rating):
    """Оценка должна быть от 1 до 5 (MinValueValidator/MaxValueValidator на модели)."""
    # Act
    response = auth_client.post(
        "/api/my-books/", {"book_id": book.id, "status": "finished", "rating": rating}
    )

    # Assert
    assert response.status_code == 400


@pytest.mark.django_db
def test_update_nonexistent_entry_returns_404(auth_client):
    """PATCH к несуществующей записи отвечает 404, а не 500."""
    # Act
    response = auth_client.patch(
        "/api/my-books/99999/", {"status": "finished"}, content_type="application/json"
    )

    # Assert
    assert response.status_code == 404


@pytest.mark.django_db
def test_filter_by_nonexistent_status_returns_empty_list(auth_client, user_book):
    """
    Фильтр по значению, которого нет ни у одной записи, не падает —
    просто возвращает пустой список (django-filter на CharField без строгой
    валидации choices на уровне FilterSet).
    """
    # Act
    response = auth_client.get("/api/my-books/?status=dropped")

    # Assert
    assert response.status_code == 200
    assert response.data["count"] == 0


@pytest.mark.django_db
def test_notes_field_accepts_long_text(auth_client, book):
    """notes — TextField без ограничения длины, длинный текст должен приниматься."""
    # Arrange — без пробела на конце: DRF CharField обрезает края (trim_whitespace=True)
    long_notes = "Заметка. " * 999 + "Заметка."

    # Act
    response = auth_client.post(
        "/api/my-books/", {"book_id": book.id, "status": "reading", "notes": long_notes}
    )

    # Assert
    assert response.status_code == 201
    assert response.data["notes"] == long_notes