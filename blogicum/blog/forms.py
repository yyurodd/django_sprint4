from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Post, Comment, Category, Location

User = get_user_model()


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        exclude = ('author', 'created_at')  # Исключаем автора и дату создания
        widgets = {
            'pub_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
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
        
        if self.instance.pk:  # При редактировании существующего поста
            if self.instance.pub_date:
                # Конвертируем в локальное время и правильный формат
                local_time = timezone.localtime(self.instance.pub_date)
                formatted_time = local_time.strftime('%Y-%m-%dT%H:%M')
                self.initial['pub_date'] = formatted_time
        else:  # При создании нового поста
            now = timezone.now()
            local_time = timezone.localtime(now)
            formatted_time = local_time.strftime('%Y-%m-%dT%H:%M')
            self.initial['pub_date'] = formatted_time


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