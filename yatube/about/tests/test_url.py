from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class PostsURLTests(TestCase):
    def setUp(self):
        """Создаем неавторизованный клиент"""
        self.guest_client = Client()

    """Прверяем доступность статических страниц"""
    def test_url_static(self):
        about_urls_name = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }
        for address in about_urls_name.keys():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(
                    response,
                    self.about_urls_name[address]
                )
