from multiprocessing import context
from django.utils import timezone
from django.shortcuts import render, redirect
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.views import View
from .models import Notification, Post, Comment ,UserProfile, Image, Tag
from .forms import PostForm, CommentForm, ShareForm, ExploreForm
from django.urls import reverse_lazy
from django.contrib.auth.mixins import UserPassesTestMixin,LoginRequiredMixin


from django.views.generic.edit import UpdateView, DeleteView


class PostListView(LoginRequiredMixin,View):

    def get(self, request,  *args, **kwargs):
        logged_in_user = request.user
        post = Post.objects.filter(
            author__profile__followers__in=[logged_in_user.id]
        ).order_by('-shared_on')
        form = PostForm
        share_form = ShareForm

        context ={
            'post_list' : post,
            'form' : form,
            'shareform' : share_form,
        }
        return render(request, 'social/post_list.html', context)
    
    def post(self, request,  *args, **kwargs):
        logged_in_user = request.user
        post = Post.objects.filter(
            author__profile__followers__in=[logged_in_user.id]
        )        
        form = PostForm(request.POST, request.FILES)
        share_form = ShareForm


        files = request.FILES.getlist('image')

        if form.is_valid():
            new_post = form.save(commit =False)
            new_post.author =request.user
            new_post.save()

            new_post.create_tags()

            for f in files:
                img = Image(image=f)
                img.save()
                new_post.image.add(img)

            new_post.save()
            
        context ={
            'post_list' : post,
            'form' : form,
            'share_form' : share_form
        }
        return render(request, 'social/post_list.html', context)

class PostDetailView(LoginRequiredMixin, View):

    def get(self, request, pk, *args, **kwargs):
        post = Post.objects.get(pk=pk)
        form = CommentForm

        comments = Comment.objects.filter(post=post)

        context ={
            'post' : post,
            'form' : form,
            'comments' : comments,

        }
        return render(request, 'social/post_detail.html', context)
    
    def post(self, request, pk, *args, **kwargs):
        post = Post.objects.get(pk=pk)
        form = CommentForm(request.POST)

        if form.is_valid():
            comment = form.save(commit =False)
            comment.author = request.user
            comment.post = post
            comment.save()

            comment.create_tags()



        comments = Comment.objects.filter(post=post)

        notification = Notification.objects.create(notification_type= 2, from_user= request.user, to_user= post.author, post=post)
            
        context ={
            'post' : post,
            'form' : form,
            'comments' : comments
        }
        return render(request, 'social/post_detail.html', context)



class PostEditView(UserPassesTestMixin,LoginRequiredMixin,UpdateView):
    model = Post
    fields = ['body']
    template_name = 'social/post_edit.html'


    def get_success_url(self):
        pk= self.kwargs['pk']
        return reverse_lazy('post-detail', kwargs={'pk': pk})

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author
    

 
    


class PostDeleteView(UserPassesTestMixin,LoginRequiredMixin,DeleteView):
    model = Post
    template_name = 'social/post_delete.html'
    success_url = reverse_lazy('post-list')

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

class CommentDeleteView(UserPassesTestMixin,LoginRequiredMixin,DeleteView):
    model = Comment
    template_name = 'social/comment_delete.html'

    def get_success_url(self):
        pk= self.kwargs['post_pk']
        return reverse_lazy('post-detail', kwargs={'pk': pk})

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

class UserProfileView(View):
    def get(self, request, pk, *args, **kwargs):
        profile = UserProfile.objects.get(pk=pk)
        user = profile.user
        posts = Post.objects.filter(author=user)

        followers = profile.followers.all()
        number_of_followers = len(followers)

        if len(followers) == 0:
                is_following =False
            
        for follower in followers:
            if follower == request.user:
                is_following =True
                break
            else:
                is_following = False
            

        context = {
            'profile' : profile,
            'user' : user,
            'posts' : posts,
            'number_of_followers' : number_of_followers,
            'is_following' : is_following,

        }

        return render(request, 'social/profile.html', context)

class ProfileEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = UserProfile
    fields = ['name', 'date_of_birth', 'gender', 'bio', 'location', 'picture'] 
    template_name = 'social/profile_edit.html'

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse_lazy('profile', kwargs={'pk': pk})


    def test_func(self):
        profile = self.get_object()
        return self.request.user == profile.user

class AddFollower(LoginRequiredMixin,View):
    def post(self, request, pk, *args, **kwargs):
        profile = UserProfile.objects.get(pk=pk)
        profile.followers.add(request.user)

        notification = Notification.objects.create(notification_type= 3, from_user= request.user, to_user= profile.user)


        return redirect('profile', pk=profile.pk)

class RemoveFollower(LoginRequiredMixin,View):
    def post(self, request, pk, *args, **kwargs):
        profile = UserProfile.objects.get(pk=pk)
        profile.followers.remove(request.user)

        return redirect('profile', pk=profile.pk)  

class AddLike(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        post = Post.objects.get(pk=pk)

        is_dislike = False

        for dislike in post.dislikes.all():
            if dislike == request.user:
                is_dislike = True
                break

        if is_dislike:
            post.dislikes.remove(request.user)

        is_like = False

        for like in post.likes.all():
            if like == request.user:
                is_like = True
                break

        if not is_like:
            post.likes.add(request.user)
            notification = Notification.objects.create(notification_type= 1, from_user= request.user, to_user= post.author, post=post)

            

        if is_like:
            post.likes.remove(request.user)
        next = request.POST.get('next', '/')
        return HttpResponseRedirect(next)

class AddDislike(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        post = Post.objects.get(pk=pk)

        is_like = False

        for like in post.likes.all():
            if like == request.user:
                is_like = True
                break

        if is_like:
            post.likes.remove(request.user)

        is_dislike = False

        for dislike in post.dislikes.all():
            if dislike == request.user:
                is_dislike = True
                break

        if not is_dislike:
            post.dislikes.add(request.user)

        if is_dislike:
            post.dislikes.remove(request.user)
                
        next = request.POST.get('next', '/')
        return HttpResponseRedirect(next)

class AddCommentLike(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        comment = Comment.objects.get(pk=pk)

        is_dislike = False

        for dislike in comment.dislikes.all():
            if dislike == request.user:
                is_dislike = True
                break

        if is_dislike:
            comment.dislikes.remove(request.user)

        is_like = False

        for like in comment.likes.all():
            if like == request.user:
                is_like = True
                break

        if not is_like:
            comment.likes.add(request.user)
            notification = Notification.objects.create(notification_type= 1, from_user= request.user, to_user= comment.author, comment=comment)


        if is_like:
            comment.likes.remove(request.user)
        next = request.POST.get('next', '/')
        return HttpResponseRedirect(next)

class AddCommentDislike(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        comment = Comment.objects.get(pk=pk)

        is_like = False

        for like in comment.likes.all():
            if like == request.user:
                is_like = True
                break

        if is_like:
            comment.likes.remove(request.user)

        is_dislike = False

        for dislike in comment.dislikes.all():
            if dislike == request.user:
                is_dislike = True
                break

        if not is_dislike:
            comment.dislikes.add(request.user)

        if is_dislike:
            comment.dislikes.remove(request.user)
                
        next = request.POST.get('next', '/')
        return HttpResponseRedirect(next)
    
class UserSearch(View):
    def get(self, request, *args, **kwargs):
        query = self.request.GET.get('query')
        profile_list = UserProfile.objects.filter(
            Q(user__username__icontains=query)
        )
        post_list =Post.objects.filter(
            Q(body__icontains=query)
        )
        context={
            'profile_list' : profile_list,
            'post_list' : post_list,
            'query' : query
        }
        return render(request, 'social/search.html', context)

class ListFollowers(View):
    def get(self, request, pk, *args, **kwargs):
        profile = UserProfile.objects.get(pk= pk)
        followers = profile.followers.all()

        context={
            'profile' : profile,
            'followers' : followers,
        }
        return render(request, 'social/followers.html', context)
class CommentReplyView(LoginRequiredMixin, View):
    def post(self, request, post_pk, pk, *args, **kwargs):
        post = Post.objects.get(pk=post_pk)
        parent_comment = Comment.objects.get(pk=pk)
        form = CommentForm(request.POST)

        if form.is_valid():
            new_comment = form.save(commit=False)
            new_comment.author = request.user
            new_comment.post = post
            new_comment.parent = parent_comment
            new_comment.save()

        notification = Notification.objects.create(notification_type= 2, from_user= request.user, to_user= parent_comment.author, comment=new_comment)

        return redirect('post-detail', pk=post_pk)

class PostNotification(View):
    def get(self, request, notification_pk, post_pk , *args, **kwargs):
        notification = Notification.objects.get(pk=notification_pk)
        post = Post.objects.get(pk=post_pk)

        notification.user_has_seen = True
        notification.save()

        return redirect('post-detail', pk= post_pk)

class FollowNotification(View):
    def get(self, request, notification_pk, profile_pk , *args, **kwargs):
        notification = Notification.objects.get(pk=notification_pk)
        profile = UserProfile.objects.get(pk=profile_pk)

        notification.user_has_seen = True
        notification.save()

        return redirect('profile', pk= profile_pk)

class SharedView(View):
    def post(self,request,pk, *args, **kwargs):
        original_post = Post.objects.get(pk=pk)
        form = ShareForm(request.POST)

        if form.is_valid():
            new_post = Post(
                shared_body = self.request.POST.get('body'),
                body =original_post.body,
                author = original_post.author,
                shared_user = request.user,
                created_on = original_post.created_on,
                shared_on = timezone.now(),

            )
            
            new_post.save()
            
            new_post.create_tags()
            for img in original_post.image.all():
                new_post.image.add(img)
            new_post.save()

        return redirect('post-list')


class ExploreView(View):
    def get(self, request, *args, **kwargs):
        explore_form = ExploreForm()
        query = self.request.GET.get('query')
        tag = Tag.objects.filter(name=query).first()

        if tag:
            posts = Post.objects.filter(tags__in=[tag])
        else:
            posts = Post.objects.all()


        context = {
            'posts' : posts,
            'tag' : tag,
            'explore_form' : explore_form,
        }
        return render(request, 'social/explore.html', context)

    def post(self, request, *args, **kwargs):
        explore_form = ExploreForm(request.POST)
        if explore_form.is_valid():
            query = explore_form.cleaned_data['query']
            tag = Tag.objects.filter(name=query).first()

            posts = None
            if tag:
                posts = Post.objects.filter(tags__in=[tag])

            if posts:
                context = {
                    'tag' : tag,
                    'posts' : posts,
                }
            else:
                context = {
                    'tag' : tag,
                }

            return HttpResponseRedirect(f'/social/explore?query={query}')
        return HttpResponseRedirect('/social/explore')
