from django import forms
from django.core.cache import cache
from django.core.paginator import Paginator
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Follow, Group, Post, User

NUMBER_OF_POST = 10
NUMBER_OF_POST_2 = 3
NUMBER_OF_TEST_POST = 13


class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test_user')

        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='the_group',
            description='Test description'
        )

        cls.group_2 = Group.objects.create(
            title='Тестовый заголовок 2',
            slug='the_group_2',
            description='Test description 2'
        )

        cls.post = [
            Post.objects.create(
                text='Тестовый пост' + str(i),
                author=cls.user,
                group=cls.group,
            )
            for i in range(NUMBER_OF_TEST_POST)
        ]
        cache.clear()

    def setUp(self):
        self.guest_client = Client()
        self.user = TaskPagesTests.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': 'the_group'}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': 'test_user'}): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': '1'}): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': '1'}): 'posts/post_create.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:index'))
        context = response.context['page_obj'].object_list
        paginator = Paginator(
            Post.objects.order_by('-pub_date'), NUMBER_OF_POST
        )
        expect_list = list(paginator.get_page(1).object_list)
        self.assertEqual(context, expect_list)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'the_group'})
        )
        context = response.context['page_obj'].object_list
        paginator = Paginator(
            Post.objects.order_by('-pub_date'), NUMBER_OF_POST
        )
        expect_list = list(paginator.get_page(1).object_list)
        self.assertEqual(context, expect_list)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'test_user'})
        )
        context = response.context['page_obj'].object_list
        paginator = Paginator(
            Post.objects.order_by('-pub_date'), NUMBER_OF_POST
        )
        expect_list = list(paginator.get_page(1).object_list)
        self.assertEqual(context, expect_list)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.authorized_client.get(reverse(
                    'posts:post_detail',
                    kwargs={'post_id': '1'})))
        context = response.context['post'].text
        expect_post = 'Тестовый пост0'
        self.assertEqual(context, expect_post)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_post_context(self):
        """Контекст страницы редактирования поста
        содержит пост, отфильтрованный по id."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': '1'})
        )
        context = response.context['post'].text
        expect_post = 'Тестовый пост0'
        self.assertEqual(context, expect_post)

    def test_post_show_on_template(self):
        """Пост появляется на главной странице, группы и профиля."""
        post = Post.objects.filter(group=self.group).order_by('-pub_date')[0]
        pages_name = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'the_group'}),
            reverse('posts:profile', kwargs={'username': 'test_user'})
        ]
        for adress in pages_name:
            response = self.authorized_client.get(adress)
            self.assertTrue(post in response.context['page_obj'].object_list)

    def test_group_post_page_show_post_not_in_group_2(self):
        """Проверка - пост не попал в другую группу."""
        post = Post.objects.filter(group=self.group).order_by('-pub_date')[0]
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'the_group_2'})
        )
        self.assertFalse(post in response.context['page_obj'].object_list)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test_user')

        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='the_group',
            description='Test description'
        )

        cls.post = [
            Post.objects.create(
                text='Тестовый пост' + str(i),
                author=cls.user,
                group=cls.group,
            )
            for i in range(NUMBER_OF_TEST_POST)
        ]

    def setUp(self):
        self.guest_client = Client()
        self.user = PaginatorViewsTest.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        """Количество постов на первой странице равно 10."""
        pages_name = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'the_group'}),
            reverse('posts:profile', kwargs={'username': 'test_user'})
        ]
        for adress in pages_name:
            response = self.authorized_client.get(adress)
            self.assertEqual(len(response.context['page_obj']), NUMBER_OF_POST)

    def test_second_page_contains_three_records(self):
        """Количество постов на второй странице равно 3."""
        pages_name = [
            reverse('posts:index') + '?page=2',
            reverse(
                'posts:group_list', kwargs={'slug': 'the_group'}) + '?page=2',
            reverse(
                'posts:profile', kwargs={'username': 'test_user'}) + '?page=2',
        ]
        for adress in pages_name:
            response = self.authorized_client.get(adress)
            self.assertEqual(
                len(response.context['page_obj']), NUMBER_OF_POST_2
            )


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test_user')
        cls.user2 = User.objects.create(username='test_user2')
        cls.user3 = User.objects.create(username='test_user3')
        cls.post = Post.objects.create(
            author=cls.user2,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = FollowTests.user
        self.user2 = FollowTests.user2
        self.user3 = FollowTests.user3
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)
        self.authorized_client3 = Client()
        self.authorized_client3.force_login(self.user3)

    def test_follow(self):
        '''Авторизованный пользователь может подписываться на других.'''
        follow_count = Follow.objects.count()
        response = self.authorized_client.post(
            reverse('posts:profile_follow', args=[self.user2]),
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            args=[self.user2])
        )
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=self.user2
            ).exists()
        )

    def test_unfollow(self):
        '''Авторизованный пользователь может отписываться.'''
        self.follow = Follow.objects.create(
            user=self.user,
            author=self.user2
        )
        follow_count = Follow.objects.count()
        response = self.authorized_client.post(
            reverse('posts:profile_unfollow', args=[self.user2]),
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            args=[self.user2])
        )
        self.assertEqual(Follow.objects.count(), follow_count - 1)
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=self.user2
            ).exists()
        )

    def test_follow_post(self):
        '''Пост есть при подписке и нет, если не подписан'''
        self.follow = Follow.objects.create(
            user=self.user,
            author=self.user2
        )
        follow_index = self.authorized_client.get(
            reverse('posts:follow_index')
        ).context['page_obj'][0]
        self.assertEqual(self.post, follow_index)
        follow_index_not_subscriber = self.authorized_client3.get(
            reverse('posts:follow_index')
        ).context['page_obj']
        self.assertNotEqual(self.post, follow_index_not_subscriber)


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='the_group',
            description='Test description'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = CacheTests.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache(self):
        """Проверка кэширования Index page"""
        new_post = Post.objects.create(
            author=self.user,
            text='Текстовый текст',
            group=self.group
        )
        response = self.authorized_client.get('posts:index').content
        new_post.delete()
        response_cache = self.authorized_client.get('posts:index').content
        self.assertEqual(response, response_cache)
        cache.clear()
        response_non_cache = self.authorized_client.get(
            reverse('posts:index')
        ).content
        self.assertNotEqual(response, response_non_cache)
