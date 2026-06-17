from django.db import models
from django.conf import settings


class Ticket(models.Model):
    """
    Заявка на оказание услуг.
    Основная сущность из ТЗ и вашей Диаграммы классов.
    """
    class Status(models.TextChoices):
        NEW = 'NEW', 'Новая'
        IN_PROGRESS = 'IN_PROGRESS', 'На рассмотрении'
        WAITING = 'WAITING', 'Ожидание клиента'
        CLOSED = 'CLOSED', 'Закрыта'
        REJECTED = 'REJECTED', 'Отклонена'
        CANCELED = 'CANCELED', 'Отменена'

    class Priority(models.TextChoices):
        LOW = 'LOW', 'Низкий'
        MEDIUM = 'MEDIUM', 'Средний'
        HIGH = 'HIGH', 'Высокий'

    # Связи (Foreign Keys) — это то, что на Диаграмме классов называется "один ко многим"
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='tickets', 
        verbose_name="Автор (Клиент)",
        help_text="Клиент, создавший заявку"
    )
    executor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_tickets', 
        verbose_name="Исполнитель",
        help_text="Сотрудник, назначенный на заявку"
    )

    # Атрибуты заявки из Диаграммы классов
    title = models.CharField(max_length=200, verbose_name="Тема заявки")
    description = models.TextField(verbose_name="Описание проблемы")
    contact_info = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="Контактная информация"
    )
    
    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default=Status.NEW, 
        verbose_name="Статус"
    )
    priority = models.CharField(
        max_length=10, 
        choices=Priority.choices, 
        default=Priority.MEDIUM, 
        verbose_name="Приоритет"
    )

    # Даты (из Диаграммы классов)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    # Дополнительные поля из бизнес-логики (Модуль 2)
    appointment_time = models.DateTimeField(
        blank=True, 
        null=True, 
        verbose_name="Время приёма в офисе"
    )
    rejection_reason = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Причина отклонения"
    )
    
    # Документы (Модуль 9 — связь с Аниным модулем)
    contract_pdf = models.FileField(
        upload_to='contracts/%Y/%m/%d/', 
        blank=True, 
        null=True, 
        verbose_name="PDF-договор"
    )

    def __str__(self):
        return f"Заявка #{self.id} - {self.title}"

    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
        ordering = ['-created_at']  # Новые заявки сверху


class TicketStatusHistory(models.Model):
    """
    История изменений статусов заявки.
    Нужно для "лога аудита" из ТЗ (раздел 4.1.3.2).
    """
    ticket = models.ForeignKey(
        Ticket, 
        on_delete=models.CASCADE, 
        related_name='status_history',
        verbose_name="Заявка"
    )
    old_status = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        verbose_name="Предыдущий статус"
    )
    new_status = models.CharField(
        max_length=20,
        verbose_name="Новый статус"
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Кто изменил"
    )
    changed_at = models.DateTimeField(auto_now_add=True, verbose_name="Когда изменено")
    comment = models.TextField(blank=True, null=True, verbose_name="Комментарий к изменению")

    def __str__(self):
        return f"{self.ticket} : {self.old_status} → {self.new_status}"

    class Meta:
        verbose_name = "История статусов"
        verbose_name_plural = "История статусов"
        ordering = ['-changed_at']


class Comment(models.Model):
    """
    Комментарий к заявке.
    Может быть обычным (виден клиенту) или внутренней заметкой (только для сотрудников).
    """
    ticket = models.ForeignKey(
        Ticket, 
        on_delete=models.CASCADE, 
        related_name='comments', 
        verbose_name="Заявка"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        verbose_name="Автор комментария"
    )
    
    text = models.TextField(verbose_name="Текст комментария")
    is_internal = models.BooleanField(
        default=False, 
        verbose_name="Внутренняя заметка",
        help_text="Если True, то комментарий виден только сотрудникам"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата изменения")

    def __str__(self):
        return f"Комментарий к Заявке #{self.ticket.id} от {self.author}"

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"
        ordering = ['created_at']




from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver


@receiver(pre_save, sender=Ticket)
def capture_old_status(sender, instance, **kwargs):
    """
    Сигнал перед сохранением заявки.
    Запоминаем старый статус, чтобы потом записать его в историю.
    """
    if instance.pk:  # Если заявка уже существует (не новая)
        try:
            old_instance = Ticket.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except Ticket.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=Ticket)
def log_status_change(sender, instance, created, **kwargs):
    """
    Сигнал после сохранения заявки.
    Записывает изменение статуса в историю.
    """
    old_status = getattr(instance, '_old_status', None)
    
    if created:
        # Заявка только что создана
        TicketStatusHistory.objects.create(
            ticket=instance,
            old_status=None,
            new_status=instance.status,
            changed_by=instance.author,
            comment="Заявка создана"
        )
    elif old_status != instance.status:
        # Статус изменился
        TicketStatusHistory.objects.create(
            ticket=instance,
            old_status=old_status,
            new_status=instance.status,
            changed_by=instance.author,  # Здесь должен быть текущий пользователь
            comment=f"Статус изменен с '{old_status}' на '{instance.status}'"
        )