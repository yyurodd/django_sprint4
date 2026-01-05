from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Post, Comment, Category, Location

User = get_user_model()


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'text', 'pub_date', 'location', 'category', 'image']
        widgets = {
            'pub_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'location': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Показываем только опубликованные категории и местоположения
        # Если нет опубликованных, показываем все (для случая, когда админ еще не опубликовал)
        published_categories = Category.objects.filter(is_published=True)
        if published_categories.exists():
            self.fields['category'].queryset = published_categories
        else:
            # Если нет опубликованных категорий, показываем все
            self.fields['category'].queryset = Category.objects.all()
        
        published_locations = Location.objects.filter(is_published=True)
        if published_locations.exists():
            self.fields['location'].queryset = published_locations
        else:
            # Если нет опубликованных местоположений, показываем все
            self.fields['location'].queryset = Location.objects.all()
        
        # Делаем категорию обязательной
        self.fields['category'].required = True
        # Местоположение необязательное - добавляем пустое значение
        self.fields['location'].required = False
        self.fields['location'].empty_label = "Выберите местоположение (необязательно)"
        
        # Устанавливаем значение по умолчанию для даты публикации (текущее время)
        if not self.instance.pk:  # Только при создании нового поста
            now = timezone.now()
            # Форматируем для datetime-local input
            local_time = now.strftime('%Y-%m-%dT%H:%M')
            self.fields['pub_date'].initial = local_time


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3}),
        }


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class UserProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']