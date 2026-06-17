from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Настройка админки для кастомной модели пользователя"""
    model = CustomUser
    
    # Поля, которые отображаются в списке пользователей
    list_display = ('username', 'email', 'surname', 'name', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    
    # Поля в форме редактирования
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {
            'fields': ('surname', 'name', 'patronymic', 'birth_date', 'role', 'contact_phone')
        }),
    )
    
    # Поля в форме создания пользователя
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Дополнительная информация', {
            'fields': ('surname', 'name', 'patronymic', 'birth_date', 'role', 'contact_phone', 'email')
        }),
    )