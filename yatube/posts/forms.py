from django.forms import ModelForm
from posts.models import Comment, Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        labels = {
            'text': 'Текст поста',
            'group': 'Группа'
        }
        help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост'
        }
        fields = ['text', 'group', 'image']


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        labels = {'text': 'Добавить комментарий'}
        help_texts = {'text': 'Текст комментария'}
