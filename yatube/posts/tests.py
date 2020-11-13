import tempfile

from django.test import TestCase, Client, override_settings
from django.urls import reverse

from .models import User, Post, Group, Follow, Comment
from django.conf import settings

from django.core.cache import cache


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
        cache.clear()
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
        for i in ("", self.user, f'{self.user}/{self.post.id}'):
            response = self.client.get(f'/{i}/')
            self.assertContains(response, "My new post(refactor)!")


class Error404Test(TestCase):
    def test_404_page(self):
        # создаем подключение
        self.client = Client()
        # Получаем ответ со странице /404
        response = self.client.get("/404/")
        # Проверяем соответствует ли ответ, коду ошибки
        self.assertEqual(response.status_code, 404)
        # Проверяем, что если режим отладки отключен, мы используем заданный шаблон
        if not settings.DEBUG:
            self.assertTemplateUsed(
                response, template_name="misc/404.html"
            )
        # Проверяем передана ли в контекст нужная переменная
        self.assertEqual(response.context["path"], "/404/")


class ImageTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="makson", email="q@q.com", password="123456")
        self.group = Group.objects.create(title="testGroup", slug="testGroup")
        # Создаем пост
        self.post = Post.objects.create(text="text without image", author=self.user)
        # Логинемся
        self.client.force_login(self.user)
        # Создаем временную директорию
        with tempfile.TemporaryDirectory() as temp_directory:
            with override_settings(MEDIA_ROOT=temp_directory):
                # Загружаем картинку , которая находится в указанной директории
                with open('posts/test/test_image.jpg', 'rb') as img:
                    # Определяем параметры
                    params = {'username': self.user.username, 'post_id': self.post.id}
                    payload = {'text': 'text with image', 'image': img, 'group': self.group.id}
                    # Получаем ответ отредактированного поста
                    response = self.client.post(reverse('post_edit', kwargs=params), data=payload, follow=True)
                    self.assertContains(response, '<img')

    # Проверка наличия картинки на главной странице
    def test_image_on_index(self):
        response = self.client.get('', follow=True)
        self.assertContains(response, '<img')

    # Проверка наличия изображения на странице профиля
    def test_image_on_profile_page(self):
        response = self.client.get('/makson/')
        self.assertContains(response, '<img')

    # Проверка наличия изображения на странице группы
    def test_image_on_group_page(self):
        response = self.client.get('/group/testGroup', follow=True)
        self.assertContains(response, '<img')

    # Проверка защиты от загрузки файлов не-графических форматов
    def test_no_image_upload(self):
        with open('posts/admin.py', 'rb') as img:
            # Определяем параметры
            params = {'username': self.user.username, 'post_id': self.post.id}
            payload = {'text': 'text with no_image_file', 'image': img, 'group': self.group.id}
            # Получаем ответ отредактиоваррного поста
            response = self.client.post(reverse('post_edit', kwargs=params), data=payload, follow=True)
            # Проверяем, что в ответе нет тега <img>
            self.assertNotContains(response, '<img')
            # Проверяем, что в БД по только одна запись
            self.assertEqual(Post.objects.count(), 1)


class CacheTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="test", email="w@q.com", password="1234567")
        # Создаем пост
        self.post = Post.objects.create(text="test1", author=self.user)

    def test_cache_index_page(self):
        response = self.client.get("")
        self.assertContains(response, 'test1')
        self.post = Post.objects.create(text="test2", author=self.user)
        response = self.client.get("")
        self.assertNotContains(response, 'test2')


class FollowTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='test', password='12345678q')
        self.post = Post.objects.create(text="new_test", author=self.user)
        self.user2 = User.objects.create_user(username='test2', password='12345678q')

    def test_following(self):
        # Проверяю возможность подписки авторизованного пользователя, на другого пользователя
        self.client.force_login(self.user2)
        self.client.get(f'/{self.user}/follow/')
        self.assertEqual(Follow.objects.filter(author=self.user).count(), 1)

    def test_unfollowing(self):
        # Проверяю возможность отписки авторизованного пользователя, от другого пользователя
        self.client.force_login(self.user2)
        self.client.get(f'/{self.user}/unfollow/')
        self.assertEqual(Follow.objects.filter(author=self.user).count(), 0)

    def test_check_post_follower(self):
        # Проверка появления новой записи в ленте подписанного пользователя на другого пользователя
        self.client.force_login(self.user2)
        self.client.get(f'/{self.user}/follow/')
        response = self.client.get('/follow/')
        self.assertContains(response, 'new_test')

    def test_check_post_follower(self):
        # Проверка отсутствия новой записи в ленте не подписанного пользователя на другого пользователя
        self.client.force_login(self.user2)
        response = self.client.get('/follow/')
        self.assertNotContains(response, 'new_test')


class CommentTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='TestComment', password='12345678q')
        self.post = Post.objects.create(text="New_post", author=self.user)
        self.user2 = User.objects.create_user(username='Test2', password="123456789q")

    def test_comment_post_auth_user(self):
        # Логинемся и комментируем пост, после проверяем наличия комментария
        self.client.force_login(self.user2)
        self.client.post(f'/{self.user}/{self.post.id}/comment', {"text": 'best_comment'})
        response = self.client.get(f'/{self.user}/{self.post.id}/')
        self.assertContains(response, "best_comment")

    def test_comment_post_not_auth_user(self):
        # Не логинемся и комментируем пост, после проверяем отсутствие комментария
        self.client.post(f'/{self.user}/{self.post.id}/comment', {"text": 'best_comment'})
        response = self.client.get(f'/{self.user}/{self.post.id}/')
        self.assertNotContains(response, "best_comment")
