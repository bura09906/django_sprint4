from django.contrib import admin

from .models import Category, Location, Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'pub_date',
        'is_published',
        'category',
        'author',
        'location',
    )
    list_editable = (
        'is_published',
    )
    search_fields = (
        'author',
        'location',
        'category',
    )
    list_filter = (
        'category',
    )


admin.site.register(Category)
admin.site.register(Location)
