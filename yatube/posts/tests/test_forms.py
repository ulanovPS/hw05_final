import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import get_object_or_404
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Comment, Group, Post

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        """Создаем записи в базе данных для тестирования"""
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
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

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        """Создаем пользователя и авторизируем"""
        self.user = User.objects.create_user(username='pavel')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post(self):
        """Тест шаблона добавления нового поста"""
        count_posts = Post.objects.count()
        form_data = {
            'text': 'Данные из формы',
            'group': self.group.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        post_1 = Post.objects.get(id=self.group.id)
        author_1 = User.objects.get(username=self.user)
        group_1 = Group.objects.get(title=self.group.title)
        self.assertEqual(Post.objects.count(), count_posts + 1)
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': self.user}
        ))
        self.assertEqual(post_1.text, form_data['text'])
        self.assertEqual(author_1.username, self.user.username)
        self.assertEqual(group_1.title, self.group.title)

    def test_guest_new_post(self):
        """Неавторизоанный пользователь не может создавать посты"""
        form_data = {
            'text': 'Пост от неавторизованного пользователя',
            'group': self.group.id
        }
        self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertFalse(Post.objects.filter(
            text=form_data['text']).exists())

    def test_authorized_edit_post(self):
        """Авторизованный пользователь может редактировать"""
        form_data = {
            'text': 'Данные из формы',
            'group': self.group.id
        }
        old_group_response = self.authorized_client.get(
            reverse('posts:group_list', args=(self.group.slug,))
        )
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        post_2 = Post.objects.get(id=self.group.id)
        self.client.get(f'/{self.user}/{post_2.id}/edit/')
        form_data = {
            'text': 'Измененный текст',
            'group': self.group2.id
        }
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
        self.assertEqual(post_2.text, form_data['text'])
        new_group_response = self.authorized_client.get(
            reverse('posts:group_list', args=(self.group2.slug,))
        )
        """Проверяем что записей со старой группой нет"""
        new_count = new_group_response.context['page_obj'].paginator.count
        old_count = old_group_response.context['page_obj'].paginator.count
        self.assertEqual(new_count, old_count + 1)

    def test_post_with_picture(self):
        """Проверка создания поста с картинкой"""
        """Авторизированным пользователем"""
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
            'text': 'Пост с картинкой',
            'group': self.group.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        post_1 = Post.objects.get(id=self.group.id)
        author_1 = User.objects.get(username=self.user)
        group_1 = Group.objects.get(title='Заголовок для тестовой группы')
        self.assertEqual(Post.objects.count(), count_posts + 1)
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': self.user}
        ))
        self.assertEqual(post_1.text, 'Пост с картинкой')
        self.assertEqual(author_1.username, self.user.username)
        self.assertEqual(group_1.title, 'Заголовок для тестовой группы')


class CommentTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            author=User.objects.create_user(username='pavel',
                                            email='test1@mail.ru',
                                            password='test_pass',),
            text='Тестовая запись для создания 1 поста',
            group=Group.objects.create(
                title='Заголовок для 1 тестовой группы',
                slug='test_slug1'))

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.user = User.objects.create_user(username='pavel1')
        self.authorized_client.force_login(self.user)

    def test_guest_new_comment(self):
        """Неавторизоанный пользователь не может создавать комментарии"""
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
        self.assertFalse(Comment.objects.filter(
            text=form_data['text']).exists()
        )

    def test_authorized_new_comment(self):
        """Авторизированный пользователь может создавать комментарии"""
        posts1 = Post.objects.first()
        comment_count = Comment.objects.filter(post=posts1.pk).count()
        form_data = {
            'text': 'Комментарий от авторизированного пользователя',
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': posts1.pk}
            ),
            data=form_data,
            follow=True,
        )
        self.assertTrue(get_object_or_404(
            Comment,
            text=form_data['text'],
        ))
        """Проверяем что коментарий добавился"""
        self.assertEqual(comment_count + 1, Comment.objects.count())
        """Проверяем редирект на страницу Детали поста"""
        self.assertRedirects(response, f'/posts/{self.post.id}/')
