from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BookViewSet, RegisterView, TagViewSet, UserBookViewSet

router = DefaultRouter()
router.register("books", BookViewSet, basename="book")
router.register("tags", TagViewSet, basename="tag")
router.register("my-books", UserBookViewSet, basename="userbook")

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("", include(router.urls)),
]
