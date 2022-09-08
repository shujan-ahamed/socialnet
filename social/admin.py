from django.contrib import admin
from .models import Post, Comment, UserProfile, Notification


# Register your models here.
admin.site.register(Post),
admin.site.register(Comment),
admin.site.register(UserProfile),
admin.site.register(Notification),

