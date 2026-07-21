from django.contrib import admin

from .models import Book, Tag, UserBook


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "genre", "year_published"]
    search_fields = ["title", "author"]
    list_filter = ["genre"]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name"]


@admin.register(UserBook)
class UserBookAdmin(admin.ModelAdmin):
    list_display = ["user", "book", "status", "rating"]
    list_filter = ["status"]
