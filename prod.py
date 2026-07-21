"""
Настройки для продакшена.

DEBUG всегда False, ALLOWED_HOSTS и SECRET_KEY обязаны прийти из
переменных окружения (без дефолтов "на всякий случай" — если их
не задали, приложение должно упасть при старте, а не тихо работать
в небезопасном режиме).
"""
from decouple import Csv, config

from .base import *  # noqa: F401,F403

DEBUG = False

# whitenoise нужен только в проде — в dev статику раздаёт сам Django (DEBUG=True).
MIDDLEWARE = [
    MIDDLEWARE[0],  # SecurityMiddleware  # noqa: F405
    "whitenoise.middleware.WhiteNoiseMiddleware",
    *MIDDLEWARE[1:],  # noqa: F405
]

# В проде эти значения обязаны быть заданы явно — никаких дефолтов.
SECRET_KEY = config("SECRET_KEY")
ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv())

# Базовые security-заголовки для продакшена за HTTPS.
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 7  # 1 неделя, увеличивать постепенно
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Сжатая раздача статики через whitenoise — не нужен отдельный CDN/nginx
# для pet-проекта такого размера.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}