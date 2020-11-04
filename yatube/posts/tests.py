from django.test import TestCase, Client
from django.urls import reverse

from .models import User, Post


class TestProfile(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="makson", email="q@q.com", password="123456")

    def test_new_user(self):
        response = self.client.get("/makson/", follow=True)
        # проверяем что страница найдена
        self.assertEqual(response.status_code, 200, msg="Такого профиля не создано")


class CreatePostTest(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.user = User.objects.create_user(username="makson", email="q@q.com", password="123456")

    def test_publish_post(self):
        # Проверка, что авторизованный пользователь может опубликовать пост (new)
        self.client.force_login(self.user)
        new_post_response = self.client.get("/new/", follow=True)
        self.assertEqual(new_post_response.status_code, 200)

    def test_publish_login_required(self):
        # Проверка, что неавторизованный посетитель не может опубликовать пост
        # (его редиректит на страницу входа)
        response = self.client.get("/new/")
        self.assertRedirects(
            response,
            "/auth/login/?next=/new/",
        )

    def test_after_publish_post_on_all_page(self):
        # Логинемся
        self.client.force_login(self.user)
        # Создаем пост
        self.post = Post.objects.create(text="My new post", author=self.user)
        # Проверяем наличие поста на главной странцие, странице пользователя, странице отдельного поста
        for i in ("", self.user, f'{self.user}/{self.post.id}'):
            response = self.client.get(f'/{i}/')
            self.assertContains(response, "My new post")

    def test_edit_published_post(self):
        # Логинемся
        self.client.force_login(self.user)
        # Создаем пост
        self.post = Post.objects.create(text="My new post", author=self.user)
        # Изменяем пост
        self.client.post(
                reverse("post_edit", kwargs={"username": "makson", "post_id": self.post.id}),
                {"text": "My new post(refactor)!"},
                follow=True,
            )
        # Проверяем наличие измененного поста на главной странцие, странице пользователя, странице отдельного поста
        for i in ("", self.user, f'{self.user}/{self.post.id+1}'):
            response = self.client.get(f'/{i}/')
            self.assertContains(response, "My new post(refactor)!")
