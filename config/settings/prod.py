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
