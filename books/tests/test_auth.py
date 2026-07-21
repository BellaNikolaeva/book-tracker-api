"""Тесты на /api/auth/ — регистрация, логин, обновление токена."""
import pytest
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


# --- register ---

@pytest.mark.django_db
def test_register_creates_user(client):
    """Регистрация с корректными данными создаёт пользователя и отвечает 201."""
    # Arrange — данные для регистрации
    payload = {"username": "newbie", "password": "strongpass123"}

    # Act
    response = client.post("/api/auth/register/", payload)

    # Assert
    assert response.status_code == 201
    assert User.objects.filter(username="newbie").exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "payload, reason",
    [
        pytest.param(
            {"username": "bella", "password": "strongpass123"},
            "username занят",
            id="duplicate_username",
        ),
        pytest.param(
            {"username": "shortpass", "password": "123"},
            "пароль короче минимальной длины",
            id="password_too_short",
        ),
    ],
)
def test_register_rejects_invalid_data(client, user, payload, reason):
    """Регистрация отклоняет некорректные данные (дубликат username, слишком короткий пароль)."""
    # Arrange — `user` фикстура уже создала username="bella"

    # Act
    response = client.post("/api/auth/register/", payload)

    # Assert
    assert response.status_code == 400, f"Ожидали 400: {reason}"


# --- login ---

@pytest.mark.django_db
def test_login_returns_tokens(client, user):
    """Успешный логин возвращает пару access/refresh токенов."""
    # Act
    response = client.post(
        "/api/auth/login/", {"username": user.username, "password": "testpass123"}
    )

    # Assert
    assert response.status_code == 200
    assert "access" in response.data
    assert "refresh" in response.data


@pytest.mark.django_db
@pytest.mark.parametrize(
    "username, password",
    [
        pytest.param("bella", "wrongpassword", id="wrong_password"),
        pytest.param("ghost", "whatever123", id="nonexistent_user"),
    ],
)
def test_login_rejects_invalid_credentials(client, user, username, password):
    """Логин отклоняет неверный пароль и несуществующего пользователя одинаково — 401."""
    # Act
    response = client.post("/api/auth/login/", {"username": username, "password": password})

    # Assert
    assert response.status_code == 401


# --- refresh ---

@pytest.mark.django_db
def test_refresh_returns_new_access_token(client, user):
    """Валидный refresh-токен выдаёт новый access-токен."""
    # Arrange — генерируем настоящий refresh-токен напрямую, без похода через /login/
    refresh = RefreshToken.for_user(user)

    # Act
    response = client.post("/api/auth/refresh/", {"refresh": str(refresh)})

    # Assert
    assert response.status_code == 200
    assert "access" in response.data


@pytest.mark.django_db
def test_refresh_rejects_invalid_token(client):
    """Мусорная строка вместо refresh-токена отклоняется с 401."""
    # Act
    response = client.post("/api/auth/refresh/", {"refresh": "not-a-real-token"})

    # Assert
    assert response.status_code == 401


# --- негативные и граничные случаи ---

@pytest.mark.django_db
@pytest.mark.parametrize(
    "payload, missing_field",
    [
        pytest.param({"password": "strongpass123"}, "username", id="missing_username"),
        pytest.param({"username": "someone"}, "password", id="missing_password"),
    ],
)
def test_register_requires_all_fields(client, payload, missing_field):
    """Регистрация без обязательного поля отклоняется с 400, а не 500."""
    # Act
    response = client.post("/api/auth/register/", payload)

    # Assert
    assert response.status_code == 400
    assert missing_field in response.data


@pytest.mark.django_db
def test_register_rejects_blank_username(client):
    """Пустая строка в username не проходит валидацию (не то же самое, что 'поле отсутствует')."""
    # Act
    response = client.post("/api/auth/register/", {"username": "", "password": "strongpass123"})

    # Assert
    assert response.status_code == 400


@pytest.mark.django_db
def test_register_trims_whitespace_from_username(client):
    """
    DRF CharField по умолчанию обрезает пробелы по краям (trim_whitespace=True).
    Значит ' bella_ws ' при регистрации сохраняется как 'bella_ws', и логин
    без пробелов успешно совпадает — это защищает от опечаток при регистрации.
    """
    # Arrange
    client.post("/api/auth/register/", {"username": " bella_ws ", "password": "strongpass123"})

    # Act
    response = client.post(
        "/api/auth/login/", {"username": "bella_ws", "password": "strongpass123"}
    )

    # Assert
    assert response.status_code == 200


@pytest.mark.django_db
def test_login_requires_both_fields(client, user):
    """Логин без пароля отклоняется с 400 (валидация полей), а не с 401 (неверные креды)."""
    # Act
    response = client.post("/api/auth/login/", {"username": user.username})

    # Assert
    assert response.status_code == 400


@pytest.mark.django_db
def test_refresh_requires_token_field(client):
    """Запрос на /refresh/ без поля refresh отклоняется с 400."""
    # Act
    response = client.post("/api/auth/refresh/", {})

    # Assert
    assert response.status_code == 400


@pytest.mark.django_db
def test_register_username_max_length(client):
    """
    Django User.username ограничен 150 символами — значение длиннее должно
    отклоняться, а не обрезаться молча.
    """
    # Arrange
    too_long_username = "a" * 151

    # Act
    response = client.post(
        "/api/auth/register/", {"username": too_long_username, "password": "strongpass123"}
    )

    # Assert
    assert response.status_code == 400