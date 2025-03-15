from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import SubscriptionViewSet, SubscriptionListViewSet

router = DefaultRouter()
router.register(
    r'users/subscriptions',
    SubscriptionListViewSet,
    basename='subscriptions')

urlpatterns = router.urls + [
    path('users/<int:id>/subscribe/',
         SubscriptionViewSet.as_view({'post': 'create', 'delete': 'destroy'})),
]
