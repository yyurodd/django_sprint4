from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse, reverse_lazy
from django.db.models import Count
from django.core.paginator import Paginator
from django.contrib.auth.forms import UserCreationForm
from django import forms

from .models import Category, Post, Comment
from .forms import PostForm, CommentForm, UserRegistrationForm, UserProfileEditForm

User = get_user_model()


def index(request):
    # На главной странице показываем только опубликованные посты
    # с опубликованными категориями и не отложенные (для всех пользователей)
    post_list = Post.objects.filter(
        is_published=True,
        category__is_published=True,
        pub_date__lte=timezone.now()
    ).select_related(
        'category', 'location', 'author'
    ).annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date')
    
    # Пагинация - 10 постов на страницу
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'post_list': page_obj.object_list,
    }
    return render(request, 'blog/index.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related('category', 'location', 'author'),
        pk=post_id
    )
    
    # Проверяем доступ для неавторизованных пользователей
    if not request.user.is_authenticated or request.user != post.author:
        if (not post.is_published or 
            not post.category.is_published or 
            post.pub_date > timezone.now()):
            return render(request, 'pages/404.html', status=404)
    
    comments = post.comments.select_related('author').all()
    comment_form = CommentForm()
    
    context = {
        'post': post,
        'comments': comments,
        'form': comment_form,
    }
    return render(request, 'blog/detail.html', context)


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )
    
    post_list = Post.objects.filter(
        category=category,
        is_published=True,
        pub_date__lte=timezone.now()
    ).select_related('category', 'location', 'author').annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date')
    
    # Пагинация - 10 постов на страницу
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'page_obj': page_obj,
        'post_list': page_obj.object_list,
    }
    return render(request, 'blog/category.html', context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    
    # Получаем посты пользователя
    post_list = Post.objects.filter(author=user).select_related(
        'category', 'location'
    ).annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date')
    
    # Для других пользователей скрываем неопубликованные посты
    if request.user != user:
        post_list = post_list.filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now()
        )
    
    # Пагинация - 10 постов на страницу
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'profile': user,
        'page_obj': page_obj,
        'post_list': page_obj.object_list,
    }
    return render(request, 'blog/profile.html', context)


# CBV для регистрации
class RegistrationView(CreateView):
    form_class = UserRegistrationForm
    template_name = 'registration/registration_form.html'
    success_url = reverse_lazy('login')


# CBV для создания поста
class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('blog:profile', kwargs={'username': self.request.user.username})


# CBV для редактирования поста
class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id' 
    
    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author
    
    def handle_no_permission(self):
        post = self.get_object()
        return redirect('blog:post_detail', post_id=post.pk)
    
    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.object.pk})


# CBV для удаления поста
class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'
    
    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author
    
    def get_success_url(self):
        return reverse('blog:profile', kwargs={'username': self.request.user.username})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .forms import PostForm
        context['form'] = PostForm(instance=self.object)
        return context



@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
    return redirect('blog:post_detail', post_id=post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id, post_id=post_id)
    
    if request.user != comment.author:
        return redirect('blog:post_detail', post_id=post_id)
    
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = CommentForm(instance=comment)
    
    return render(request, 'blog/comment.html', {
        'form': form,
        'comment': comment,
        'post': comment.post
    })


@login_required
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id, post_id=post_id)
    
    if request.user != comment.author:
        return redirect('blog:post_detail', post_id=post_id)
    
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)
    
    return render(request, 'blog/comment.html', {
        'comment': comment,
        'post': comment.post
    })

class UserProfileEditView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileEditForm
    template_name = 'blog/user.html'
    
    def get_object(self):
        return self.request.user
    
    def get_success_url(self):
        return reverse('blog:profile', kwargs={'username': self.request.user.username})
    