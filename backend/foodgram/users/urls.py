from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserProfileView, AvatarView, UserViewSet, SetPasswordView

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="users")

urlpatterns = [
    path("users/set_password/", SetPasswordView.as_view(), name="set-password"),
    path("", include(router.urls)),
    path("users/<int:id>/", UserProfileView.as_view(), name="user-profile"),
    path("users/me/avatar/", AvatarView.as_view(), name="avatar-update"),
]
