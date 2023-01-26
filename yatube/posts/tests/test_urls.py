from http import HTTPStatus

from django.test import Client, TestCase

from posts.models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create(username='User')
        cls.another_user = User.objects.create(username='another_user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.post = Post.objects.create(
            text='Тестовая запись',
            author=cls.user,
        )
        cls.postFromAnotherUser = Post.objects.create(
            text='Тестовая запись от другого пользователя',
            author=cls.another_user,
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Описание группы',
        )

    def test_pages_for_everyone(self):
        pages_urls = [
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user.username}/',
            f'/posts/{self.post.id}/',
        ]
        for url in pages_urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    f'Page {url} is not OK'
                )

    def test_pages_for_authorized_user(self):
        pages_urls = [
            f'/posts/{self.post.id}/edit/',
            '/create/'
        ]
        for url in pages_urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK,
                                 f'Page {url} is not OK')

    def test_private_pages_as_guest(self):
        pages_urls = [
            f'/posts/{self.post.id}/edit/',
            '/create/'
        ]
        for url in pages_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTrue(response.status_code in (301, 302),
                                f'Page {url} is not OK')

    def test_post_edit_page_as_not_author(self):
        response = self.authorized_client.get(
            f'/posts/{self.postFromAnotherUser.id}/edit/',)
        self.assertTrue(response.status_code in (301, 302), HTTPStatus.OK)

    def test_unexisting_page_url_exists_at_desired_location(self):
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/sasdss/': 'core/404.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)