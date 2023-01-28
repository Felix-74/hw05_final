from http import HTTPStatus

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Comment, Follow, Group, Post

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            pub_date='Тестовая дата',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        templates_page_names = {
            reverse('posts:group_list',
                    args=(self.group.slug,)): 'posts/group_list.html',
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:profile',
                    args=(self.user.username,)): 'posts/profile.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_detail',
                    args=(self.post.pk,)): 'posts/post_detail.html',
            reverse('posts:post_edit',
                    args=(self.post.pk,)): 'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_group_page_correct_context(self):
        response = self.guest_client.get(reverse(
            'posts:group_list', args=(self.group.slug,)))
        self.check_page_obj(response)
        self.assertTrue(
            'group' in response.context, 'Context doesn\'t contains a group')
        self.assertIsInstance(
            response.context['group'], Group,
            '"group" is not instance of Group')
        self.check_post_fields(response.context['page_obj'][0])

    def test_author_page_correct_context(self):
        response = self.guest_client.get(reverse(
            'posts:profile', args=(self.user.username,)))
        self.check_page_obj(response)
        self.assertTrue(
            'author' in response.context, 'Context doesn\'t contains a author')
        self.assertIsInstance(
            response.context['author'], User,
            '"author" is not instance of User')
        self.check_post_fields(response.context['page_obj'][0])

    def test_index_page_correct_context(self):
        response = self.guest_client.get(reverse('posts:index'))
        self.check_page_obj(response)
        self.check_post_fields(response.context['page_obj'][0])

    def test_post_detail_correct_context(self):
        response = self.guest_client.get(reverse(
            'posts:post_detail', args=(self.post.pk,)))
        self.assertTrue(
            'post' in response.context, 'Context doesn\'t contains a post')
        self.check_post_fields(response.context['post'])

    def check_page_obj(self, response):
        self.assertTrue(
            'page_obj' in response.context,
            'Context doesn\'t contains a page_obj')
        self.assertEqual(
            response.context['page_obj'].number,
            1,
            'Object list should has length=1')
        self.assertIsInstance(
            response.context['page_obj'][0], Post, 'First object is not Post')

    def check_post_fields(self, post):
        posts_dict = {
            post.pub_date: self.post.pub_date,
            post.text: self.post.text,
            post.author: self.user,
            post.group: self.group,
            post.image: self.post.image
        }
        for post_param, test_post_param in posts_dict.items():
            with self.subTest(
                    post_param=post_param,
                    test_post_param=test_post_param):
                self.assertEqual(post_param, test_post_param, )

    def test_create_post_show_correct_context2(self):
        """Шаблоны create и edit сформированы с правильным контекстом."""
        namespace_list = [
            reverse('posts:post_create'),
            reverse('posts:post_edit', args=[self.post.pk])
        ]
        for reverse_name in namespace_list:
            response = self.authorized_client.get(reverse_name)
            form_fields = {
                'text': forms.fields.CharField,
                'group': forms.fields.ChoiceField,
            }
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context['form'].fields[value]
                    self.assertIsInstance(form_field, expected)

    def test_post_another_group(self):
        response = self.authorized_client.get(
            reverse('posts:group_list', args=(self.group.slug,)))

        page_posts = response.context['page_obj']
        self.assertEqual(len(page_posts), 1)
        post = response.context['page_obj'][0]
        self.assertTrue(post.text, 'Тестовый текст')


class PostPaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        total_posts_count = 13
        for post_number in range(total_posts_count):
            cls.post = Post.objects.create(
                text='Тестовый текст',
                author=cls.user,
                group=cls.group
            )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_posts(self):
        namespace_list = {
            'posts:index': reverse('posts:index'),
            'posts:group_list': reverse(
                'posts:group_list', args=(self.group.slug,)),
            'posts:profile': reverse(
                'posts:profile', args=(self.user.username,)),
        }
        count_posts = settings.PAGE_LIMIT
        for template, reverse_name in namespace_list.items():
            response = self.guest_client.get(reverse_name)
            self.assertEqual(len(response.context['page_obj']), count_posts)

    def test_another_page_contains_valid_posts(self):
        page = 2
        namespace_list = {
            'posts:index': reverse('posts:index') + f'?page={page}',
            'posts:group_list': reverse(
                'posts:group_list',
                args=(self.group.slug,)) + f'?page={page}',
            'posts:profile': reverse(
                'posts:profile',
                args=(self.user.username,)) + f'?page={page}',
        }

        count_posts = Post.objects.count() - (settings.PAGE_LIMIT * (page - 1))
        for template, reverse_name in namespace_list.items():
            response = self.guest_client.get(reverse_name)
            self.assertEqual(len(response.context['page_obj']), count_posts)


class CommentTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
        )
        cls.comment = Comment.objects.create(
            text='Тестовый комментарий',
            post=cls.post,
            author=cls.user
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_add_comment(self):
        """После успешной отправки комментарий появляется на странице поста."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', args=[self.post.pk]))
        count_comments = 1
        self.assertEqual(len(response.context['comments']), count_comments)
        first_object = response.context['comments'][0]
        comment_text = first_object.text
        self.assertTrue(comment_text, 'Тестовый текст')


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title="Тестовый заголовок",
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            pub_date='Тестовая дата',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()

    def test_cache_index(self):
        """Тест кэширования главной страницы."""
        response = self.authorized_client.get(reverse('posts:index'))
        post = Post.objects.get(pk=1)
        post.text = 'Измененный текст'
        post.save()
        second_response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.content, second_response.content)
        post.delete()
        cache.clear()
        third_response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response.content, third_response.content)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_follower = User.objects.create_user(
            username='follower',
            email='test_follower_@mail.ru',
            password='test_password')
        cls.user_following = User.objects.create_user(
            username='following',
            email='test_following_@mail.ru',
            password='test_password')
        cls.post = Post.objects.create(
            author=cls.user_following,
            text='Тестовая запись для тестирования')

    def setUp(self):
        self.client_auth_follower = Client()
        self.client_auth_following = Client()
        self.client_auth_follower.force_login(self.user_follower)
        self.client_auth_following.force_login(self.user_following)

    def test_profile_follow(self):
        """Авторизованный пользователь может
        подписываться на других пользователей.
        """
        self.client_auth_follower.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user_following.username}))
        count_follower = 1
        self.assertEqual(Follow.objects.all().count(), count_follower)

    def test_profile_unfollow(self):
        """Авторизованный пользователь может
        удалять других пользователей из подписок.
        """
        self.client_auth_follower.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.user_following.username}))
        count_follower = 0
        self.assertEqual(Follow.objects.all().count(), count_follower)

    def test_subscription(self):
        """Новая запись появляется в ленте тех, кто на него подписан."""
        Follow.objects.create(user=self.user_follower,
                              author=self.user_following)
        response = self.client_auth_follower.get(reverse('posts:follow_index'))
        post_text = response.context["page_obj"][0].text
        self.assertEqual(post_text, 'Тестовая запись для тестирования')

    def test_no_subscription(self):
        """Новая запись не появляется в ленте тех, кто не подписан."""
        posts_response = self.client_auth_follower.get(reverse(
            'posts:follow_index'))
        self.assertTrue(
            'page_obj' in posts_response.context,
            'Context doesn\'t contains a page_obj')

        posts_counts = posts_response.context['page_obj'].number
        Follow.objects.create(user=self.user_follower,
                              author=self.user_following)
        new_posts_response = self.client_auth_follower.get(reverse(
            'posts:follow_index'))
        self.assertEqual(
            new_posts_response.context['page_obj'].number,
            posts_counts,
            'New post was in unsubscribed user\'s feed')
