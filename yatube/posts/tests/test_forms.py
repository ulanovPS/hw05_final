import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        """Создаем записи в базе данных для тестирования"""

        cls.group = Group.objects.create(
            title=('Заголовок для тестовой группы'),
            slug='test_slug23',
            description='Тестовое описание'
        )

        cls.group2 = Group.objects.create(
            title=('Заголовок для тестовой группы 2'),
            slug='test_slug2',
            description='Тестовое описание 2'
        )

        cls.user = User.objects.create_user(username='pavel')

    def setUp(self):
        self.guest_client = Client()
        """Создаем пользователя и авторизируем"""
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post(self):
        """Тест шаблона добавления нового поста"""
        count_posts = Post.objects.count()
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
            'text': 'Данные из формы',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        post_1 = Post.objects.last()
        self.assertEqual(Post.objects.count(), count_posts + 1)
        self.assertEqual(post_1.text, form_data['text'])
        self.assertEqual(post_1.group.title, self.group.title)
        self.assertEqual(post_1.author, self.user)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_guest_new_post(self):
        """Неавторизоанный пользователь не может создавать посты"""
        form_data = {
            'text': 'Пост от неавторизованного пользователя',
            'group': self.group.id
        }
        first_count = Post.objects.count()
        self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(
            Post.objects.count(),
            first_count
        )

    def test_authorized_edit_post(self):
        """Авторизованный пользователь может редактировать"""
        form_data = {
            'text': 'Данные из формы',
            'group': self.group.id
        }
        """Создаем пост"""
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        post_2 = Post.objects.get(id=self.group.id)
        form_data = {
            'text': 'Измененный текст',
            'group': self.group2.id
        }
        """Изменяем пост"""
        response_edit = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': post_2.id}
            ),
            data=form_data,
            follow=True,
        )
        post_2 = Post.objects.get(id=self.group.id)
        self.assertEqual(response_edit.status_code, HTTPStatus.OK)
        """Проверяем что запись изменилась"""
        self.assertEqual(post_2.text, form_data['text'])
        self.assertEqual(post_2.group.pk, form_data['group'])

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)


class CommentTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_pavel = User.objects.create_user(
            username='pavel',
            email='pavel@gmail.ru',
            password='test_pass'
        ),
        cls.user_author = User.objects.create_user(
            username='author',
            email='author@gmail.ru',
            password='test_pass'
        ),
        cls.group = Group.objects.create(
            title='Заголовок для 1 тестовой группы',
            slug='test_slug1'
        )

        cls.post = Post.objects.create(
            author=User.objects.create_user(username=cls.user_author),
            text='Тестовая запись для создания 1 поста',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.post.author)

    def test_guest_new_comment(self):
        """Неавторизоанный пользователь не может создавать комментарии"""
        count_first = Comment.objects.count()
        form_data = {
            'text': 'Комментарий от неавторизованного пользователя',
        }
        self.guest_client.post(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.pk}
            ),
            data=form_data,
            follow=True,
        )
        count_second = Comment.objects.count()
        """Проверяем что комментарий не создался"""
        self.assertEqual(count_first, count_second)

    def test_authorized_new_comment(self):
        """Авторизированный пользователь может создавать комментарии"""
        comment_count = self.post.comments.count()
        form_data = {
            'text': 'Комментарий от авторизированного пользователя',
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.pk}
            ),
            data=form_data,
            follow=True,
        )
        """Проверяем что коментарий добавился"""
        self.assertEqual(
            comment_count + 1,
            Comment.objects.filter(post=self.post.pk).count()
        )
        """Проверяем редирект на страницу Детали поста"""
        self.assertRedirects(response, f'/posts/{self.post.pk}/')
