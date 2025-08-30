from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import UserViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = SimpleRouter()
router.register("users", UserViewSet, basename="user")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/jwt/create", TokenObtainPairView.as_view(), name="jwt_create"),
    path("auth/jwt/refresh", TokenRefreshView.as_view(), name="jwt_refresh"),
]
