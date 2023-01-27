from django.test import TestCase
from posts.models import Group, Post, User

NUMBER_OF_SIMBOL = 16
NUMBER_OF_SIMBOL_STR = 15


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=str('ф') * NUMBER_OF_SIMBOL,
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        group = PostModelTest.group
        test_models_expect = {
            str('ф') * NUMBER_OF_SIMBOL_STR: post,
            'Тестовая группа': group,
        }
        for expect, model in test_models_expect.items():
            with self.subTest(field=expect):
                self.assertEqual(str(model), expect)
