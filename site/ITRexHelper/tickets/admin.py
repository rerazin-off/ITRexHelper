from django.contrib import admin
from .models import Ticket, Comment, TicketStatusHistory


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    """Настройка админки для модели Заявка"""
    list_display = ('id', 'title', 'author', 'executor', 'status', 'priority', 'created_at')
    list_filter = ('status', 'priority', 'created_at')
    search_fields = ('title', 'description', 'author__username')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('author', 'title', 'description', 'contact_info')
        }),
        ('Статус и обработка', {
            'fields': ('status', 'priority', 'executor', 'appointment_time', 'rejection_reason')
        }),
        ('Документы', {
            'fields': ('contract_pdf',)
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Настройка админки для модели Комментарий"""
    list_display = ('ticket', 'author', 'is_internal', 'created_at')
    list_filter = ('is_internal', 'created_at')
    search_fields = ('text', 'ticket__title')
    ordering = ('-created_at',)


@admin.register(TicketStatusHistory)
class TicketStatusHistoryAdmin(admin.ModelAdmin):
    """Настройка админки для модели История статусов"""
    list_display = ('ticket', 'old_status', 'new_status', 'changed_by', 'changed_at')
    list_filter = ('new_status', 'changed_at')
    ordering = ('-changed_at',)