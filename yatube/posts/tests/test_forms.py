import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.forms import CommentForm
from posts.models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
NUMBER_OF_POST = 10
NUMBER_OF_TEST_POST = 13


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user = PostFormTests.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в post."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': self.post.text,
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                ('posts:profile'), kwargs={'username': 'test_user'}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                author=self.user,
                text=self.post.text,
                group=self.group.id,
                image=self.post.image
            ).exists()
        )

    def test_post_edit(self):
        """Проверка изменения формы редактирования поста."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый измененный пост',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse(
                ('posts:post_edit'), kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                ('posts:post_detail'), kwargs={'post_id': self.post.id}))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый измененный пост',
                group=self.group.id,
            ).exists()
        )

    def test_comment_appears_in_post(self):
        """Проверка добавления комментария авторизованным пользователем."""
        form = CommentForm(data={
            'text': 'some comment',
        })
        self.assertTrue(form.is_valid())

        response = self.authorized_client.post(
            reverse('posts:add_comment', args=[self.post.pk]),
            data=form.data,
            follow=True
        )

        self.assertEqual(self.post.comments.last().text, form.data['text'])

        self.assertRedirects(response, reverse(
            'posts:post_detail',
            args=[self.post.pk])
        )
