from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator

from .forms import PostForm
from .models import User, Post, Group


def index(request):
    post_list = Post.objects.order_by('-pub_date').all()
    paginator = Paginator(post_list, 10)  # показывать по 10 записей на странице.

    page_number = request.GET.get('page')  # переменная в URL с номером запрошенной страницы
    page = paginator.get_page(page_number)  # получить записи с нужным смещением
    return render(
        request,
        'index.html',
        {'page': page, 'paginator': paginator}
    )


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


def profile(request, username):
    # тут тело функции
    profile = get_object_or_404(User.objects.annotate(posts_count=Count("posts")), username=username)
    post_list = (
        Post
            .objects
            .filter(author=profile)
            .order_by('-pub_date')
            .all()
    )
    count_post = post_list.count()
    paginator = Paginator(post_list, 5)  # показывать по 5 записей на странице.
    page_number = request.GET.get('page')  # переменная в URL с номером запрошенной страницы
    page = paginator.get_page(page_number)  # получить записи с нужным смещением
    context = {
        "post_list": post_list,
        "count_post": count_post,
        "profile": profile,
        'page': page,
        'paginator': paginator
    }
    return render(request, 'profile.html', context)


def post_view(request, username, post_id):
    profile = get_object_or_404(User.objects.annotate(posts_count=Count("posts")), username=username)
    post = get_object_or_404(
        Post.objects.select_related("author")
            .select_related("group"),
        pk=post_id, author=profile
    )
    context = {
        "profile": profile,
        "post": post,
    }
    return render(request, "post.html", context)


# @login_required
# def post_edit(request, username, post_id):
#     # тут тело функции. Не забудьте проверить,
#     # что текущий пользователь — это автор записи.
#     # В качестве шаблона страницы редактирования укажите шаблон создания новой записи
#     # который вы создали раньше (вы могли назвать шаблон иначе)
#     post = get_object_or_404(Post, id=post_id)
#     # проверка, что текущий юзер и автор поста совпадают
#     if request.user == post.author:
#         if request.method == "POST":
#             form = PostForm(request.POST or None, files=request.FILES or None, instance=post)
#             if form.is_valid():
#                 post = form.save(commit=False)
#                 post.author = request.user
#                 post.save()
#                 return redirect("post", username=username, post_id=post_id)
#         else:
#             form = PostForm(instance=post)
#             context = {
#                 "form": form,
#                 "post": post
#             }
#         return render(request, "new_post.html", context)
#     return redirect("post", username=username, post_id=post_id)


@login_required
def post_edit(request, username, post_id):
    profile = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, pk=post_id, author=profile)
    if request.user != profile:
        return redirect('post', username=username, post_id=post_id)
    # добавим в form свойство files
    form = PostForm(request.POST or None, files=request.FILES or None, instance=post)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect("post", username=request.user.username, post_id=post_id)

    return render(
        request, 'new_post.html', {'form': form, 'post': post},
    )