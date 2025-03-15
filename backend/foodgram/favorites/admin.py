from favorites.models import Favorite
from django.contrib import admin


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe', 'added_at')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user', 'recipe')