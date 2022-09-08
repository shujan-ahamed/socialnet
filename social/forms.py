from email.mime import image
from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):
    body = forms.CharField(
        label = '',
        widget= forms.Textarea(attrs={
            'rows' : '3',
            'placeholder' : 'say something...'
        })
    )
    image = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'multiple': True
            })
    )

    class Meta:
        model = Post
        fields =['body']

class CommentForm(forms.ModelForm):
    comment = forms.CharField(
        label = '',
        widget= forms.Textarea(attrs={
            'rows' : '2',
            'placeholder' : 'comment here'
        })
    )

    class Meta:
        model = Comment
        fields =['comment']

class ShareForm(forms.Form):
    body = forms.CharField(
        label='',
        widget= forms.Textarea(attrs={
            'rows' : '2',
            'placeholder' : 'say something...'
        })
    )
class ExploreForm(forms.Form):
    query = forms.CharField(
        label='',
        widget= forms.Textarea(attrs={
            'placeholder' : 'Explore...'
        })
    )