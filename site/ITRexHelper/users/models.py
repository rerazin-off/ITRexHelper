from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    """
    Кастомная модель пользователя.
    Объединяет классы 'Пользователь', 'Клиент' и 'Администратор' из UML-диаграммы.
    """
    class Role(models.TextChoices):
        CLIENT = 'CLIENT', 'Клиент'
        STAFF = 'STAFF', 'Сотрудник поддержки'
        ADMIN = 'ADMIN', 'Администратор'

    # Атрибуты из вашей Диаграммы классов (раздел 3.4 отчета)
    surname = models.CharField(max_length=100, verbose_name="Фамилия")
    name = models.CharField(max_length=100, verbose_name="Имя")
    patronymic = models.CharField(max_length=100, blank=True, null=True, verbose_name="Отчество")
    birth_date = models.DateField(blank=True, null=True, verbose_name="Дата рождения")
    
    # Роль пользователя (вместо наследования классов)
    role = models.CharField(
        max_length=10, 
        choices=Role.choices, 
        default=Role.CLIENT, 
        verbose_name="Роль"
    )
    
    contact_phone = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        verbose_name="Контактный телефон"
    )

    def __str__(self):
        return f"{self.surname} {self.name} ({self.get_role_display()})"

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"