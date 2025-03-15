from django.contrib import admin

from subscribers.models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author', 'created_at')
    search_fields = ('user__username', 'author__username')
    list_filter = ('user', 'author')