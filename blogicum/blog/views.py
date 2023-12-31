from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView

from .forms import CommentForm, PostForm, UserForm
from .models import Category, Comment, Post, User
from core.utils import page_object


def post_list(request):
    posts = Post.objects.select_related(
        'category',
        'location',
        'author',
    ).filter(
        category__is_published=True,
        is_published=True,
        pub_date__lte=timezone.now(),
    ).annotate(comment_count=Count('comments')).order_by('-pub_date')
    context = {
        'page_obj': page_object(posts, request.GET.get('page'))
    }
    return render(request, 'blog/index.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if (post.author != request.user
        and (post.is_published is False
             or post.category.is_published is False
             or post.pub_date > timezone.now())):
        return render(request, 'pages/404.html', status=404)
    comments = post.comments.select_related('author')
    context = {
        'post': post,
        'form': CommentForm(),
        'comments': comments
    }
    return render(request, 'blog/detail.html', context)


class PostMixin:
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["view_name"] = self.request.resolver_match.view_name
        return context


class PostCreatView(LoginRequiredMixin, PostMixin, CreateView):

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:profile',
                       kwargs={'username': self.request.user})


class PostUpdateView(LoginRequiredMixin, PostMixin, UpdateView):
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, pk=self.kwargs['post_id'])
        if instance.author != self.request.user:
            return redirect('blog:post_detail', post_id=self.kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('blog:post_detail',
                       kwargs={'post_id': self.kwargs['post_id']})


class PostDeleteView(LoginRequiredMixin, PostMixin, DeleteView):
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, pk=self.kwargs['post_id'])
        if instance.author != self.request.user:
            return redirect('blog:post_detail', post_id=self.kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.form_class(instance=self.object)
        return context

    def get_success_url(self):
        return reverse('blog:profile',
                       kwargs={'username': self.request.user})


class CommentMixin:
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def get_success_url(self):
        return reverse('blog:post_detail',
                       kwargs={'post_id': self.kwargs['post_id']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["view_name"] = self.request.resolver_match.view_name
        return context


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/detail.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(Post, id=self.kwargs['post_id'])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:post_detail',
                       kwargs={'post_id': self.kwargs['post_id']})


class CommentUpdateView(LoginRequiredMixin, CommentMixin, UpdateView):
    form_class = CommentForm

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Comment, pk=self.kwargs['comment_id'])
        if instance.author != self.request.user:
            return redirect('blog:post_detail', post_id=self.kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)


class CommentDeleteView(LoginRequiredMixin, CommentMixin, DeleteView):

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Comment, pk=self.kwargs['comment_id'])
        if instance.author != self.request.user:
            return redirect('blog:post_detail', post_id=self.kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)


def profile(request, username):
    profile = get_object_or_404(User, username=username)
    page_obj = profile.posts.order_by(
        '-pub_date',
    ).annotate(comment_count=Count('comments'))
    if profile != request.user:
        page_obj = page_obj.filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now(),
        )
    context = {
        'profile': profile,
        'page_obj': page_object(page_obj, request.GET.get('page')),
    }
    return render(request, 'blog/profile.html', context)


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserForm
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse('blog:profile',
                       kwargs={'username': self.request.user})


class CategoryDetailView(DetailView):
    model = Category
    template_name = 'blog/category.html'
    context_object_name = 'category'
    slug_url_kwarg = 'category_slug'

    def dispatch(self, request, *args, **kwargs):
        get_object_or_404(
            self.model,
            is_published=True,
            slug=self.kwargs['category_slug']
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        posts = self.get_object().posts.filter(
            is_published=True,
            pub_date__lte=timezone.now(),
        ).order_by('-pub_date').annotate(
            comment_count=Count('comments')
        )
        context['page_obj'] = page_object(posts, self.request.GET.get('page'))
        return context
