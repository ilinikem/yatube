from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
import datetime

from .forms import PostForm
from .models import User, Post, Group



def index(request):
    latest = Post.objects.order_by("-pub_date")
    # Create query for order_by
    start_date = datetime.date(1854, 7, 7)
    end_date = datetime.date(1854, 7, 21)
    author = User.objects.get(username="leo")
    posts = Post.objects.filter(text__contains="Утро").filter(author=author).filter(
        pub_date__range=(start_date, end_date))
    return render(request, "index.html", {"posts": posts})


def group_posts(request, slug):
    # функция get_object_or_404 получает по заданным критериям объект из базы данных
    # или возвращает сообщение об ошибке, если объект не найден

    group = get_object_or_404(Group, slug=slug)

    # Метод .filter позволяет ограничить поиск по критериям. Это аналог добавления
    # условия WHERE group_id = {group_id}
    posts = Post.objects.filter(group=group).order_by("-pub_date")[:12]
    return render(request, "group.html", {"group": group, "posts": posts})


@login_required()
def new_post(request):
    # проверим, пришёл ли к нам POST-запрос или какой-то другой:
    if request.method == 'POST':
        # создаём объект формы класса ContactForm и передаём в него полученные данные
        form = PostForm(request.POST)
        # проверяем данные на валидность:
        # ... здесь код валидации ...

        if form.is_valid():
            # обрабатываем данные формы, используя значения словаря form.cleaned_data
            # возвращаем результат
            # Функция redirect перенаправляет пользователя
            # на другую страницу сайта, чтобы защититься
            # от повторного заполнения формы, если посетитель
            # сайта случайно перезагрузит страницу
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('index')

        # если не сработало условие if form.is_valid() и данные не прошли валидацию
        # сработает следующий блок кода,
        # иначе команда return прервала бы дальнейшее исполнение функции

        # вернём пользователю страницу с HTML-формой и передадим полученный объект формы на страницу,
        # чтобы вернуть информацию об ошибке

        # заодно автоматически заполним прошедшими валидацию данными все поля,
        # чтобы не заставлять пользователя второй раз заполнять их
        return render(request, 'new_post.html', {'form': form})

    form = PostForm()
    return render(request, 'new_post.html', {'form': form})
