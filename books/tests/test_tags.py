"""Тесты на /api/tags/."""
import pytest

from books.models import Tag

# --- list & retrieve (доступны анонимно) ---

@pytest.mark.django_db
def test_anonymous_can_list_tags(client, tag):
    """Список тегов открыт без авторизации."""
    # Act
    response = client.get("/api/tags/")

    # Assert
    assert response.status_code == 200
    assert response.data["count"] == 1


@pytest.mark.django_db
def test_anonymous_can_retrieve_tag(client, tag):
    """Детали конкретного тега открыты без авторизации."""
    # Act
    response = client.get(f"/api/tags/{tag.id}/")

    # Assert
    assert response.status_code == 200
    assert response.data["name"] == tag.name


@pytest.mark.django_db
def test_retrieve_nonexistent_tag_returns_404(client):
    """Запрос несуществующего тега отвечает 404."""
    # Act
    response = client.get("/api/tags/99999/")

    # Assert
    assert response.status_code == 404


# --- запись доступна только авторизованным ---

@pytest.mark.django_db
def test_anonymous_cannot_create_tag(client):
    """Анонимный пользователь не может создать тег."""
    # Act
    response = client.post("/api/tags/", {"name": "фэнтези"})

    # Assert
    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_authenticated_user_can_create_tag(auth_client):
    """Авторизованный пользователь может создать тег."""
    # Act
    response = auth_client.post("/api/tags/", {"name": "фэнтези"})

    # Assert
    assert response.status_code == 201
    assert Tag.objects.filter(name="фэнтези").exists()


@pytest.mark.django_db
def test_cannot_create_duplicate_tag(auth_client, tag):
    """Тег с уже существующим именем не создаётся повторно."""
    # Act
    response = auth_client.post("/api/tags/", {"name": tag.name})

    # Assert
    assert response.status_code == 400


@pytest.mark.django_db
def test_anonymous_cannot_update_tag(client, tag):
    """Анонимный пользователь не может изменить тег."""
    # Act
    response = client.patch(
        f"/api/tags/{tag.id}/", {"name": "обновлённый тег"}, content_type="application/json"
    )

    # Assert
    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_authenticated_user_can_update_tag(auth_client, tag):
    """Авторизованный пользователь может изменить тег, изменение сохраняется."""
    # Act
    response = auth_client.patch(
        f"/api/tags/{tag.id}/", {"name": "обновлённый тег"}, content_type="application/json"
    )

    # Assert
    assert response.status_code == 200
    tag.refresh_from_db()
    assert tag.name == "обновлённый тег"


@pytest.mark.django_db
def test_anonymous_cannot_delete_tag(client, tag):
    """Анонимный пользователь не может удалить тег — он остаётся в БД."""
    # Act
    response = client.delete(f"/api/tags/{tag.id}/")

    # Assert
    assert response.status_code in (401, 403)
    assert Tag.objects.filter(id=tag.id).exists()


@pytest.mark.django_db
def test_authenticated_user_can_delete_tag(auth_client, tag):
    """Авторизованный пользователь может удалить тег."""
    # Act
    response = auth_client.delete(f"/api/tags/{tag.id}/")

    # Assert
    assert response.status_code == 204
    assert not Tag.objects.filter(id=tag.id).exists()


# --- негативные и граничные случаи ---

@pytest.mark.django_db
def test_create_tag_requires_name(auth_client):
    """Тег без name отклоняется с 400."""
    # Act
    response = auth_client.post("/api/tags/", {})

    # Assert
    assert response.status_code == 400
    assert "name" in response.data


@pytest.mark.django_db
def test_create_tag_rejects_blank_name(auth_client):
    """Пустая строка в name не проходит валидацию."""
    # Act
    response = auth_client.post("/api/tags/", {"name": ""})

    # Assert
    assert response.status_code == 400


@pytest.mark.django_db
def test_create_tag_rejects_name_over_max_length(auth_client):
    """Tag.name ограничено 50 символами — значение длиннее должно отклоняться."""
    # Arrange
    too_long_name = "а" * 51

    # Act
    response = auth_client.post("/api/tags/", {"name": too_long_name})

    # Assert
    assert response.status_code == 400


@pytest.mark.django_db
def test_create_tag_at_exact_max_length_is_allowed(auth_client):
    """Ровно 50 символов — граничное значение, должно приниматься (не off-by-one)."""
    # Arrange
    exactly_max_name = "а" * 50

    # Act
    response = auth_client.post("/api/tags/", {"name": exactly_max_name})

    # Assert
    assert response.status_code == 201


@pytest.mark.django_db
def test_update_nonexistent_tag_returns_404(auth_client):
    """PATCH к несуществующему тегу отвечает 404."""
    # Act
    response = auth_client.patch(
        "/api/tags/99999/", {"name": "что угодно"}, content_type="application/json"
    )

    # Assert
    assert response.status_code == 404


@pytest.mark.django_db
def test_delete_nonexistent_tag_returns_404(auth_client):
    """DELETE к несуществующему тегу отвечает 404, а не 204."""
    # Act
    response = auth_client.delete("/api/tags/99999/")

    # Assert
    assert response.status_code == 404