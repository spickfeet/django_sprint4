from datetime import datetime

from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render, get_object_or_404, redirect

from .forms import PostForm, CommentForm, UserForm
from .models import Post, Category, User, Comment


NUMBER_OF_PAGINATOR_PAGES = 10


def get_published_posts(**extra_filters):
    """Возвращает опубликованные посты с базовыми фильтрами."""
    base_filters = {
        'is_published': True,
        'category__is_published': True,
        'pub_date__lte': datetime.now(),
    }
    # Объединяем базовые фильтры с дополнительными
    filters = {**base_filters, **extra_filters}
    return get_posts(**filters)


def get_posts(**kwargs):
    """Получение постов"""
    return Post.objects.select_related(
        'category',
        'location',
        'author'
    ).annotate(comment_count=Count('comments')
               ).filter(**kwargs).order_by('-pub_date')


def get_paginator(request, queryset,
                  number_of_pages=NUMBER_OF_PAGINATOR_PAGES):
    """Пагинация"""
    paginator = Paginator(queryset, number_of_pages)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def index(request):
    """Главная страница"""
    posts = get_published_posts()
    page_obj = get_paginator(request, posts)
    context = {'page_obj': page_obj}
    return render(request, 'blog/index.html', context)


def category_posts(request, category_slug):
    """Посты в категории"""
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True)
    posts = get_published_posts(category=category)
    page_obj = get_paginator(request, posts)
    context = {'category': category,
               'page_obj': page_obj}
    return render(request, 'blog/post_list.html', context)


def post_detail(request, post_id):
    """Описание поста"""
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        post = get_object_or_404(
            Post,
            id=post_id,
            is_published=True,
            category__is_published=True,
            pub_date__lte=datetime.now())
    form = CommentForm(request.POST or None)
    comments = Comment.objects.select_related(
        'author').filter(post=post)
    context = {'post': post,
               'form': form,
               'comments': comments}
    return render(request, 'blog/post_detail.html', context)


@login_required
def create_post(request):
    """Создание поста"""
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('blog:profile', request.user)
    context = {'form': form}
    return render(request, 'blog/create.html', context)


@login_required
def edit_post(request, post_id):
    """Редактирование поста"""
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('blog:post_detail', post_id)
    form = PostForm(request.POST or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id)
    context = {'form': form}
    return render(request, 'blog/create.html', context)


@login_required
def delete_post(request, post_id):
    """Удаление поста"""
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('blog:post_detail', post_id)
    form = PostForm(request.POST or None, instance=post)
    if request.method == 'POST':
        post.delete()
        return redirect('blog:index')
    context = {'form': form}
    return render(request, 'blog/create.html', context)


@login_required
def add_comment(request, post_id):
    """Добавление комментария к посту"""
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('blog:post_detail', post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    """Редактирование комментария к посту"""
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user != comment.author:
        return redirect('blog:post_detail', post_id)
    form = CommentForm(request.POST or None, instance=comment)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id)
    context = {'comment': comment,
               'form': form}
    return render(request, 'blog/comment.html', context)


@login_required
def delete_comment(request, post_id, comment_id):
    """Удаление комментария к посту"""
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user != comment.author:
        return redirect('blog:post_detail', post_id)
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id)
    context = {'comment': comment}
    return render(request, 'blog/comment.html', context)


def profile(request, username):
    """Страница пользователя"""
    profile = get_object_or_404(
        User,
        username=username)
    posts = get_posts(author=profile)
    if request.user != profile:
        posts = get_published_posts(author=profile)
    page_obj = get_paginator(request, posts)
    context = {'profile': profile,
               'page_obj': page_obj}
    return render(request, 'blog/profile.html', context)


@login_required
def edit_profile(request):
    """Редактирование страницы пользователя"""
    profile = get_object_or_404(
        User,
        username=request.user)
    form = UserForm(request.POST or None, instance=profile)
    if form.is_valid():
        form.save()
        return redirect('blog:profile', request.user)
    context = {'form': form}
    return render(request, 'blog/user.html', context)
