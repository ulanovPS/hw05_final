from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        """Создаем записи в базе данных для тестирования"""
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object___str__(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))
        group = PostModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))

    def test_verbose_name_group(self):
        """Проверяем verbose_name модели group"""
        task = PostModelTest.group
        list_verbose_name = {
            'title': 'Заголовок группы',
            'slug': 'Адрес',
            'description': 'Текст описания группы',
        }
        for field, verbose_name in list_verbose_name.items():
            with self.subTest(field=field):
                verbose = task._meta.get_field(field).verbose_name
                self.assertEqual(verbose, verbose_name)

    def test_verbose_name_post(self):
        """Проверяем verbose_name модели group"""
        task = PostModelTest.post
        list_verbose_name = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, verbose_name in list_verbose_name.items():
            with self.subTest(field=field):
                verbose = task._meta.get_field(field).verbose_name
                self.assertEqual(verbose, verbose_name)

    def test_title_help_group(self):
        """Проверяем help_text модели group"""
        task = PostModelTest.group
        list_help_text = {
            'title': 'Введите текст загловка',
            'slug': 'Введите адрес группы',
            'description': 'Введите текст описания',
        }
        for field, help_text in list_help_text.items():
            with self.subTest(field=field):
                text = task._meta.get_field(field).help_text
                self.assertEqual(text, help_text)

    def test_title_help_post(self):
        """Проверяем help_text модели post"""
        task = PostModelTest.post
        list_help_text = {
            'text': 'Введите текст поста',
            'pub_date': 'Дата создания поста',
            'author': 'Автор создания поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field, help_text in list_help_text.items():
            with self.subTest(field=field):
                text = task._meta.get_field(field).help_text
                self.assertEqual(text, help_text)
