from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from posts.models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        """Создаем записи в базе данных для тестирования"""
        cls.user_pavel = User.objects.create_user(
            username='pavel',
            email='pavel@gmail.ru',
            password='test_pass'
        )

        cls.user_author = User.objects.create_user(
            username='test_user',
            email='test@gmail.ru',
            password='test_pass',
        )

        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Тест для создания нового поста',
        )

        cls.group = Group.objects.create(
            title=('Заголовок для тестовой группы'),
            slug='test_slug'
        )

        cls.close_url_names = {
            f'/posts/{cls.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        cls.public_urls_name = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.post.author}/': 'posts/profile.html',
            f'/posts/{cls.post.id}/': 'posts/post_detail.html',
        }

    def setUp(self):
        """Создаем неавторизованный клиент"""
        self.guest_client = Client()
        """Создаем авторизованый клиент и авторизуем"""
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.post.author)
        """Создаем авторизованый клиент пользователь"""
        self.authorized_client_pavel = Client()
        self.authorized_client_pavel.force_login(self.user_pavel)

    def test_public_url_and_template_guest(self):
        """Проверка доступности адреса и шаблона публичных страниц гостю"""
        for address in self.public_urls_name.keys():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(
                    response,
                    self.public_urls_name[address]
                )

    def test_close_url_and_template_authorized_client(self):
        """Проверка доступности адреса и шаблона закрытых страниц
        авторизованному пользователю автору"""
        for address, template in self.close_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client_author.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_edit_post_not_author_redirect(self):
        """Страница редактирования недоступна не-автору и
        редиректит на просмотр этого же поста"""
        response = self.authorized_client_pavel.get(
            f'/posts/{self.post.pk}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, f'/posts/{self.post.pk}/')

    def test_close_url_and_redirect_guest_client(self):
        """Проверка доступности адреса закрытых страниц и
        редирект на авторизацию гостю """
        for address in self.close_url_names.keys():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertRedirects(
                    response,
                    f'/auth/login/?next={address}'
                )

    def test_add_comment_url_and_redirect(self):
        """Проверяем доступность редиректа при добавлении коментария
        авторизованным пользоватлем"""
        data = {
            'text': 'Тестовый коментарий'
        }
        response = self.authorized_client_pavel.post(
            f'/posts/{self.post.pk}/comment/',
            data=data,
        )
        self.assertRedirects(
            response,
            f'/posts/{self.post.pk}/',
        )
        """Проверяем не доступность создание комментария для гостя и
        редирект на страницу логин"""
        response = self.guest_client.post(
            f'/posts/{self.post.pk}/comment/',
            data=data,
        )
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{self.post.pk}/comment/'
        )

    def test_follow_unfollow_and_redirect(self):
        """Проверяем создаение подписки на автора другим пользователем"""
        response = self.authorized_client_pavel.post(
            f'/profile/{self.post.author}/follow/',
        )
        self.assertRedirects(
            response,
            f'/profile/{self.post.author}/',
        )
        """Отписываемся от автора и проверяем редирект"""
        response = self.authorized_client_pavel.post(
            f'/profile/{self.post.author}/unfollow/',
        )
        self.assertRedirects(
            response,
            f'/profile/{self.post.author}/',
        )
        """Проверяем недосутпность подписки гостем и редирект"""
        response = self.guest_client.post(
            f'/profile/{self.post.author}/follow/',
        )
        self.assertRedirects(
            response,
            f'/auth/login/?next=/profile/{self.post.author}/follow/'
        )
        """Проверяем недоступность отменить подписку дял гостя и редирект"""
        response = self.guest_client.post(
            f'/profile/{self.post.author}/unfollow/',
        )
        self.assertRedirects(
            response,
            f'/auth/login/?next=/profile/{self.post.author}/unfollow/'
        )

    def test_page_404(self):
        """Проверка обращения к несуществующей странице гостю"""
        response = self.guest_client.get('/test_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
