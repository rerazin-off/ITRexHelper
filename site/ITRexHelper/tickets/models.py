from django.db import models
from django.conf import settings


class Ticket(models.Model):

    class Status(models.TextChoices):
        NEW = 'NEW', 'Новая'
        IN_PROGRESS = 'IN_PROGRESS', 'В работе'
        WAITING = 'WAITING', 'Ожидание клиента'
        CLOSED = 'CLOSED', 'Закрыта'
        REJECTED = 'REJECTED', 'Отклонена'
        CANCELED = 'CANCELED', 'Отменена'


    class Priority(models.TextChoices):
        LOW = 'LOW', 'Низкий'
        MEDIUM = 'MEDIUM', 'Средний'
        HIGH = 'HIGH', 'Высокий'
        CRITICAL = 'CRITICAL', 'Критический'


    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tickets",
        verbose_name="Автор"
    )


    executor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tickets",
        verbose_name="Исполнитель"
    )


    title = models.CharField(
        max_length=200,
        verbose_name="Тема заявки"
    )


    description = models.TextField(
        verbose_name="Описание"
    )


    contact_info = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Контакты"
    )


    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW
    )


    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM
    )


    deadline = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Срок выполнения"
    )


    rejection_reason = models.TextField(
        null=True,
        blank=True
    )


    created_at = models.DateTimeField(
        auto_now_add=True
    )


    updated_at = models.DateTimeField(
        auto_now=True
    )


    def can_change_status(self, new_status):

        transitions = {

            self.Status.NEW:[
                self.Status.IN_PROGRESS,
                self.Status.REJECTED,
                self.Status.CANCELED
            ],

            self.Status.IN_PROGRESS:[
                self.Status.WAITING,
                self.Status.CLOSED
            ],

            self.Status.WAITING:[
                self.Status.IN_PROGRESS,
                self.Status.CLOSED
            ],

            self.Status.CLOSED:[],
            self.Status.REJECTED:[],
            self.Status.CANCELED:[]
        }


        return new_status in transitions.get(self.status, [])



    def __str__(self):
        return f"#{self.id} {self.title}"



class TicketStatusHistory(models.Model):


    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name="status_history"
    )


    old_status = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )


    new_status = models.CharField(
        max_length=20
    )


    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )


    changed_at = models.DateTimeField(
        auto_now_add=True
    )


    comment = models.TextField(
        blank=True,
        null=True
    )



    class Meta:
        ordering = ['-changed_at']



class TicketAttachment(models.Model):

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name="attachments"
    )


    file = models.FileField(
        upload_to="ticket_files/"
    )


    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )



class Comment(models.Model):


    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name="comments"
    )


    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )


    text = models.TextField()


    is_internal = models.BooleanField(
        default=False
    )


    created_at = models.DateTimeField(
        auto_now_add=True
    )


    class Meta:
        ordering = ['created_at']


class Notification(models.Model):

    class Kind(models.TextChoices):
        TICKET = 'TICKET', 'Заявка'
        COMMENT = 'COMMENT', 'Комментарий'
        STATUS = 'STATUS', 'Статус'
        CHAT = 'CHAT', 'Чат'

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_notifications'
    )

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )

    kind = models.CharField(
        max_length=20,
        choices=Kind.choices,
        default=Kind.TICKET
    )

    title = models.CharField(
        max_length=160
    )

    message = models.TextField()

    is_read = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class SupportConversation(models.Model):

    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Открыт'
        WAITING_CLIENT = 'WAITING_CLIENT', 'Ожидает клиента'
        RESOLVED = 'RESOLVED', 'Решен'

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='support_conversations'
    )

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_support_conversations'
    )

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='support_conversations'
    )

    subject = models.CharField(
        max_length=180,
        default='Чат поддержки'
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f'Чат #{self.id}: {self.client}'


class SupportMessage(models.Model):

    conversation = models.ForeignKey(
        SupportConversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='support_messages'
    )

    text = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Сообщение #{self.id}'
