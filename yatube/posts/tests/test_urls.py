from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post, User


class StaticURLTests(TestCase):
    def test_homepage(self):
        guest_client = Client()
        response = guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test_user')
        cls.user2 = User.objects.create(username='test_user2')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='the_group',
            description='Test description'
        )
        cls.urls_all = {
            '/': 'posts/index.html',
            '/group/the_group/': 'posts/group_list.html',
            '/profile/test_user2/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
        }
        cls.urls_author = {
            '/posts/1/edit/': 'posts/post_create.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.user = PostsURLTests.user
        self.user2 = PostsURLTests.user2
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)

    def test_pages_urls_for_guest_users(self):
        """Тест доступности страниц guest пользователям"""
        for address in PostsURLTests.urls_all:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_url_redirect_anonymous_on_auth_login(self):
        """Страница по адресу /create/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, (reverse('login') + '?next' + '=/create/')
        )

    def test_edit_url_redirect_anonymous_on_posts_login(self):
        """Страница по адресу /posts/1/edit/ перенаправит анонимного
        пользователя на страницу авторизации.
        """
        response = self.guest_client.get('/posts/1/edit/', follow=True)
        self.assertRedirects(
            response, (reverse('login') + '?next' + '=/posts/1/edit/')
        )

    def test_edit_url_redirect_auth_not_author_on_posts_login(self):
        """Страница по адресу /posts/1/edit/ перенаправит
        не автора поста на страницу поста.
        """
        response = self.authorized_client2.get(
            f'/posts/{self.post.pk}/edit/', follow=True
        )
        self.assertRedirects(response, (f'/posts/{self.post.pk}/'))

    def test_pages_urls_for_auth_users(self):
        """Тест доступности страниц auth пользователям"""
        for address in PostsURLTests.urls_all:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for address, template in PostsURLTests.urls_all.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_autorized_uses_correct_template(self):
        """URL-адрес create использует соответствующий шаблон."""
        response = self.authorized_client.get('/create/')
        self.assertTemplateUsed(response, 'posts/post_create.html')

    def test_urls_author_uses_correct_template(self):
        """URL-адрес edit использует соответствующий шаблон."""
        for address, template in PostsURLTests.urls_author.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_edit(self):
        """Тест доступности редактирования Автору поста"""
        response = self.authorized_client.get(f'/posts/{self.post.id}/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_page_for_auth_users(self):
        """Тест доступности unexisting auth пользователям"""
        response = self.authorized_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_unexisting_page_for_guest_users(self):
        """Тест доступности unexisting guest пользователям"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_create_url_for_auth_users(self):
        """Тест доступности create auth пользователям"""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_error_page(self):
        """Проверка, что статус ответа сервера - 404
        Проверка, что используется шаблон core/404.html
        """
        response = self.client.get('/nonexist-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
