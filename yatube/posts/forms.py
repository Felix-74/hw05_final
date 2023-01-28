from django import forms
from django.contrib.auth import get_user_model

from .models import Comment, Post

User = get_user_model()


class PostForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].widget.attrs['placeholder'] = 'Введите текст'
        self.fields['group'].empty_label = 'Выберите группу'

    class Meta:
        model = Post
        fields = (
            'text',
            'group',
            'image'
        )
        labels = {
            'text': 'Текст поста',
            'group': 'Группа',
        }
        help_text = {
            'text': 'Введите текст поста',
            'group': 'Выбрать группу',
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
