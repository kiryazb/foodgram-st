from django.contrib import admin
from django.db.models import Count

from recipes.models import Recipe


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'get_author_name')
    search_fields = (
        'name',
        'author__username',
        'author__first_name',
        'author__last_name')
    list_filter = ('author', 'name')
    readonly_fields = ('favorites_count',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(favorites_count=Count('in_favorites'))

    def favorites_count(self, obj):
        return obj.in_favorites.count()
    favorites_count.short_description = 'Добавлений в избранное'

    def get_author_name(self, obj):
        return obj.author.username
    get_author_name.short_description = 'Автор'
