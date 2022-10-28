import shutil
import tempfile
from http import HTTPStatus

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Follow, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        """Создаем записи в базе данных для тестирования"""
        # settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
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
        cls.user_pavel = User.objects.create_user(username='pavel')

        cls.group = Group.objects.create(
            title='Заголовок для 1 тестовой группы',
            slug='test_slug1'
        )

        cls.post = Post.objects.create(
            author=cls.user_pavel,
            text='1Тестовая запись для создания 1 поста',
            group=cls.group,
            image=uploaded)

    def setUp(self):
        """Создаем пользователя и авторизируем"""
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_pavel)

    def test_cache_index(self):
        """Тестируем кэш до и после очистки"""
        response = self.authorized_client.get('/')
        posts = response.content
        Post.objects.get(pk=1).delete()
        response_old = self.authorized_client.get('/')
        old_posts = response_old.content
        self.assertEqual(old_posts, posts)
        cache.clear()
        response_new = self.authorized_client.get('/')
        new_posts = response_new.content
        self.assertNotEqual(old_posts, new_posts)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            reverse('posts:group_posts'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': self.post.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': self.user_pavel}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            ): 'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                if response.status_code == HTTPStatus.OK:
                    self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Проверяем что возвращает шаблон index"""
        response = self.authorized_client.get(reverse('posts:group_posts'))
        self.assertIn('page_obj', response.context)
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object, self.post)

    def test_group_list_page_show_correct_context(self):
        """Проверяем что возвращает шаблон group_list"""
        response = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': self.post.group.slug}
        ))
        self.assertIn('page_obj', response.context)
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object, self.post)
        self.assertIn('group', response.context)
        self.assertIsInstance(response.context['group'], Group)
        self.assertEqual(response.context['group'], self.post.group)

    def test_profile_page_show_correct_context(self):
        """Проверяем шаблон profile"""
        response = self.authorized_client.get(reverse(
            'posts:profile',
            kwargs={'username': self.user_pavel}
        ))
        self.assertIn('page_obj', response.context)
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object, self.post)
        self.assertIn('author', response.context)
        self.assertIsInstance(response.context['author'], User)
        self.assertEqual(response.context['author'], self.post.author)

    def test_post_detail_page_show_correct_context(self):
        """Проверяем шаблон post_detail"""
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.pk}
        ))
        self.assertIn('post', response.context)
        self.assertIsInstance(response.context['post'], Post)
        self.assertEqual(response.context['post'], self.post)

    def test_create_page_show_correct_context(self):
        """Проверяем шаблон create"""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_create_page_show_correct_context(self):
        """Проверяем шаблон create редактирования поста по id"""
        self.authorized_client.force_login(PostTests.post.author)
        response = self.authorized_client.get(reverse(
            'posts:post_edit',
            kwargs={'post_id': PostTests.post.id}
        ))
        if response.status_code == HTTPStatus.OK:
            self.assertEqual(
                response.context['form'].instance.text,
                PostTests.post.text,
            )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        """Создаем 13 записей в базе данных для тестирования"""
        cls.author = User.objects.create_user(username='test_name')
        cls.group = Group.objects.create(
            title=('Заголовок для тестовой группы'),
            slug='test_slug2',
            description='Тестовое описание')
        cls.posts = []
        for i in range(13):
            cls.posts.append(Post(
                text=f'Тестовый пост {i}',
                author=cls.author,
                group=cls.group
            )
            )
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        """Создаем пользователя и авторизируем"""
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_first_page_contains_ten_posts(self):
        """Тестируем первую страницу Paginator"""
        list_urls = {
            reverse('posts:group_posts'): 'index',
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test_slug2'}
            ): 'group',
            reverse(
                'posts:profile',
                kwargs={'username': 'test_name'}
            ): 'profile',
        }
        for tested_url in list_urls.keys():
            response = self.client.get(tested_url)
            self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_posts(self):
        """Тестируем вторую страницу Paginator"""
        list_urls = {
            reverse('posts:group_posts') + '?page=2': 'index',
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test_slug2'}
            ) + '?page=2': 'group',
            reverse(
                'posts:profile',
                kwargs={'username': 'test_name'}
            ) + '?page=2':
            'profile',
        }
        for tested_url in list_urls.keys():
            response = self.client.get(tested_url)
            self.assertEqual(len(response.context['page_obj']), 3)


class FollowTests(TestCase):
    def setUp(self):
        """Добавляем записи в базу"""
        self.client_auth_follower = Client()
        self.client_auth_following = Client()
        self.client_pavel = Client()
        self.user_follower = User.objects.create_user(
            username='follower',
            email='test_1@gmail.com',
            password='test_pass'
        )
        self.user_following = User.objects.create_user(
            username='following',
            email='test2@gmail.com',
            password='test_pass'
        )
        self.user_pavel = User.objects.create_user(username='pavel')
        """Создаем пост пользователя following"""
        self.post = Post.objects.create(
            author=self.user_following,
            text='Тестовая запись для тестирования ленты'
        )
        """Авторизируем пользователей"""
        self.client_auth_follower.force_login(self.user_follower)
        self.client_auth_following.force_login(self.user_following)
        self.client_pavel.force_login(self.user_pavel)

    def test_follow(self):
        """Для пользователя follower проверяем создание подписки"""
        self.assertFalse(
            Follow.objects.filter(
                user=self.user_follower,
                author=self.user_following
            ).exists()
        )
        self.client_auth_follower.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user_following.username}
            )
        )
        """Проверяем что подписка создалась"""
        self.assertTrue(
            Follow.objects.filter(
                user=self.user_follower,
                author=self.user_following
            ).exists()
        )

    def test_unfollow(self):
        """Для пользователя проверяем отмену подписки"""
        Follow.objects.create(
            user=self.user_follower,
            author=self.user_following,
        )
        self.client_auth_follower.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.user_following.username}
            )
        )
        """После отмены проверяем, что записей не осталось"""
        self.assertFalse(
            Follow.objects.filter(
                user=self.user_follower,
                author=self.user_following
            ).exists()
        )
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_follow_by_myself(self):
        """Проверяем может ли пользователь подписаться на себя"""
        count_first = Follow.objects.count()
        self.client_auth_follower.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user_follower.username}
            )
        )
        """Если даже хочет, не может"""
        self.assertEqual(Follow.objects.all().count(), count_first)

    def test_subscription_feed(self):
        """Создаем подписку пользователя follower на посты following"""
        """following имеет пост"""

        Follow.objects.create(
            user=self.user_follower,
            author=self.user_following
        )
        response = self.client_auth_follower.get('/follow/')
        post_text_0 = response.context['page_obj'][0].text
        """Проверяем видит ли пост пользователя follower"""
        self.assertEqual(post_text_0, 'Тестовая запись для тестирования ленты')
        """Проверяем видит ли автор в подписках свой пост"""
        response = self.client_auth_following.get('/follow/')
        """Проверяем другим пользователем подписку, не увидит"""
        response = self.client_pavel.get('/follow/')
        self.assertNotIn(
            'Тестовая запись для тестирования ленты',
            response.context['page_obj']
        )
        self.assertEqual(post_text_0, 'Тестовая запись для тестирования ленты')
        """Так как он не может быть подписан на себя, не видит"""
        self.assertNotContains(
            response,
            'Тестовая запись для тестирования ленты'
        )
