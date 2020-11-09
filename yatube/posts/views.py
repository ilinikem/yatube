from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator

from .forms import PostForm, CommentForm
from .models import User, Post, Group, Comment


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
    # тут тело функции
    group = get_object_or_404(Group, slug=slug)
    # posts = (
    #     Post.objects.filter(group=group)
    #         .order_by("-pub_date")
    #         .all()
    # )
    posts = (
        Post.objects.filter(group=group)
        .select_related("author")
        .order_by("-pub_date")
        .all()
    )
    paginator = Paginator(posts, 2)  # показывать по 2 записей на странице.
    page_number = request.GET.get('page')  # переменная в URL с номером запрошенной страницы
    page = paginator.get_page(page_number)  # получить записи с нужным смещением
    context = {
        "posts": posts,
        "group": group,
        'page': page,
        'paginator': paginator
    }
    return render(request, 'group.html', context)


@login_required()
def new_post(request):
    # проверим, пришёл ли к нам POST-запрос или какой-то другой:
    if request.method == 'POST':
        # создаём объект формы класса ContactForm и передаём в него полученные данные
        form = PostForm(request.POST, files=request.FILES or None)
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


def post_view(request, username, post_id, form=None):
    profile = get_object_or_404(User.objects.annotate(posts_count=Count("posts")), username=username)
    post = get_object_or_404(
        Post.objects.select_related("author")
            .select_related("group"),
        pk=post_id, author=profile
    )
    if form is None:
        form = CommentForm(request.POST or None)
    # комментарии к посту
    items = Comment.objects.select_related("post", "author").filter(post=post)
    context = {
        "profile": profile,
        "post": post,
        "items": items,
        "form": form,
    }
    return render(request, "post.html", context)


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


def page_not_found(request, exception):
    # Переменная exception содержит отладочную информацию,
    # выводить её в шаблон пользователской страницы 404 мы не станем
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def add_comment(request, username, post_id):
    # убираем возможность ручного ввода адреса /username/id/comment
    # можно только через соответствующую кнопку "Добавить комментарий"
    if request.method == "GET":
        return redirect("post", username=username, post_id=post_id)
    # Получаем пост, для которого будет создан комментарий
    post = get_object_or_404(Post, id=post_id)
    if request.method == "POST":
        form = CommentForm(request.POST or None)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            return redirect("post", username=username, post_id=post_id)
    else:
        form = CommentForm(request.POST or None)
    return post_view(request, username, post_id, form=form)
