from django import forms
from django.contrib.auth.forms import UserCreationForm as OriginalUserCreationForm
from .models import Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(choices=[(i, str(i)) for i in range(1, 6)], attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Write your review here...'}),
        }
        labels = {
            'rating': 'Your Rating',
            'comment': 'Your Comment',
        }

class NewsletterForm(forms.Form):
    email = forms.EmailField(
        label='', # Empty label for cleaner UI
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your email address', 'required': 'true'})
    )

# Custom UserCreationForm for Bootstrap styling
class CustomUserCreationForm(OriginalUserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add form-control class and placeholder to all fields
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Username', # Added placeholder
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password', # Added placeholder
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password Confirmation',
        })