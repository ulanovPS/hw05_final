from django.contrib import admin
from posts.models import Comment, Follow, Group, Post


class PostAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'text',
        'pub_date',
        'author',
        'group',
    )
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'


class GroupAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'title',
        'slug',
        'description',
    )
    search_fields = ('title',)
    list_filter = ('title',)
    empty_value_display = '-пусто-'


class PostCommentAdmin(admin.ModelAdmin):
    list_display = (
        'post',
        'author',
        'text',
        'created',
    )
    search_fields = ('post', 'post')
    list_filter = ('text',)
    empty_value_display = '-пусто-'


class PostFollowAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'author',
    )
    search_fields = ('user', 'author')
    list_filter = ('author',)
    empty_value_display = '-пусто-'


admin.site.register(Post, PostAdmin)

admin.site.register(Group, GroupAdmin)

admin.site.register(Comment, PostCommentAdmin)

admin.site.register(Follow, PostFollowAdmin)
