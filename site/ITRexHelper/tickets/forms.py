from django import forms
from .models import Ticket, Comment


class TicketCreateForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'contact_info']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Тема заявки',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 4,
                'placeholder': 'Описание проблемы',
                'required': True
            }),
            'contact_info': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Телефон или Email'
            }),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text', 'is_internal']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 3,
                'placeholder': 'Введите комментарий...',
                'required': True
            }),
        }