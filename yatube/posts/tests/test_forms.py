from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse
from posts.forms import PostForm

from posts.models import Group, Post, User, Comment


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Описание группы'
        )
        cls.post = Post.objects.create(
            text='Тестовая запись',
            author=cls.user,
            group=cls.group
        )
        cls.form = PostForm()

    def test_create_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', args=(PostCreateFormTests.user,)))
        self.assertEqual(Post.objects.count(), posts_count + 1)

        last_post = Post.objects.latest('id')
        self.assertEqual(form_data.get('text'), last_post.text)
        self.assertEqual(self.user, last_post.author)
        self.assertEqual(self.group, last_post.group)

    def test_guest_create_post(self):
        last_post = Post.objects.latest('id')
        posts_count = Post.objects.count()

        form_data = {
            'text': 'Тестовый пост от неавторизованного пользователя',
            'group': self.group.pk,
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
        )

        new_last_post = Post.objects.latest('id')
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(last_post.text, new_last_post.text)
        self.assertEqual(last_post.author, new_last_post.author)
        self.assertEqual(last_post.group, new_last_post.group)
        self.assertTrue(response.status_code in (301, 302))
        self.assertEqual(response.url, '/auth/login/?next=/create/')

    def test_authorized_edit_post(self):
        create_form_data = {
            'text': 'Тестовый текст',
            'group': self.group.pk,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=create_form_data,
            follow=True,
        )

        post_edit = Post.objects.get(pk=self.post.pk)
        posts_count_before_edit = Post.objects.count()

        new_group = Group.objects.create(
            title='Новая группа',
            slug='test-slug-new',
            description='Новое описание',
        )

        edit_form_data = {
            'text': 'Измененный пост',
            'group': new_group.pk
        }
        response_edit = self.authorized_client.post(
            reverse('posts:post_edit',
                    args=(post_edit.pk,)),
            data=edit_form_data,
            follow=True,
        )
        post_edit_new = Post.objects.get(pk=self.post.pk)

        self.assertEqual(response_edit.status_code, HTTPStatus.OK)
        self.assertEqual(post_edit_new.text, edit_form_data.get('text'))
        self.assertEqual(post_edit_new.group.pk, edit_form_data['group'])
        self.assertEqual(posts_count_before_edit, Post.objects.count())

    def test_add_comment(self):
        """Комментировать посты может только авторизованный пользователь."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
