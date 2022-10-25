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
        cls.post = Post.objects.create(
            author=User.objects.create_user(username='test_user',
                                            email='test@gmail.ru',
                                            password='test_pass'),
            text='Тест для создания нового поста',)

        cls.group = Group.objects.create(
            title=('Заголовок для тестовой группы'),
            slug='test_slug'
        )

    def setUp(self):
        """Создаем неавторизованный клиент"""
        self.guest_client = Client()
        """Создаем авторизованый клиент и авторизуем"""
        self.user = User.objects.create_user(username='pavel')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_url_and_template(self):
        """Проверка доступности адреса и шаблона"""
        url_names = {
            '/': 'posts/index.html',
            '/group/test_slug/': 'posts/group_list.html',
            '/profile/test_user/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for adress, template in url_names.items():
            with self.subTest():
                response = self.guest_client.get(adress)
                if response.status_code == HTTPStatus.OK:
                    """Не авторизированный """
                    self.assertEqual(response.status_code, HTTPStatus.OK)
                    self.assertTemplateUsed(response, template)
                else:
                    """Если не доступно для не авторизированного"""
                    """Проверяем редирект"""
                    if (
                        response.status_code == HTTPStatus.FOUND
                        and adress == '/create/'
                    ):
                        self.assertRedirects(
                            response,
                            '/auth/login/?next=/create/'
                        )
                        """Проверяем для авторизированного автора"""
                        self.authorized_client.force_login(self.post.author)
                        response = self.authorized_client.get(adress)
                        self.assertEqual(response.status_code, HTTPStatus.OK)
                        self.assertTemplateUsed(response, template)
                        """Проверяем для авторизированного любого
                        пользователя"""
                        self.authorized_client.force_login(self.user)
                        response = self.authorized_client.get(adress)
                    elif (
                        response.status_code == HTTPStatus.FOUND
                        and adress == f'/posts/{self.post.id}/edit/'
                    ):
                        self.assertRedirects(
                            response,
                            '/auth/login/?next=/posts/1/edit/'
                        )
                        """Проверяем для авторизированного автора"""
                        self.authorized_client.force_login(self.post.author)
                        response = self.authorized_client.get(adress)
                        self.assertEqual(response.status_code, HTTPStatus.OK)
                        self.assertTemplateUsed(response, template)
                        """Проверяем для авторизированного любого
                        пользователя"""
                        self.authorized_client.force_login(self.user)
                        response = self.authorized_client.get(adress)
                        if response.status_code == HTTPStatus.FOUND:
                            """Если нет доступа, проверяем редирект"""
                            self.assertRedirects(
                                response,
                                '/posts/1/'
                            )

    def test_page_404(self):
        """Проверка обращения к несуществующей странице"""
        response = self.guest_client.get('/test_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_static_url_template(self):
        """Проверка доступности адреса и шаблона статических страниц"""
        url_names = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }
        for adress in url_names.keys():
            with self.subTest():
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, url_names[adress])
