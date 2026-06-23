from django.contrib import admin

from .models import (
    Comment,
    Notification,
    SupportConversation,
    SupportMessage,
    Ticket,
    TicketAttachment,
    TicketStatusHistory,
)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'executor', 'status', 'priority', 'created_at')
    list_filter = ('status', 'priority', 'created_at')
    search_fields = ('title', 'description', 'author__username', 'author__surname')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Основная информация', {
            'fields': ('author', 'title', 'description', 'contact_info')
        }),
        ('Статус и обработка', {
            'fields': ('status', 'priority', 'executor', 'deadline', 'rejection_reason')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'author', 'is_internal', 'created_at')
    list_filter = ('is_internal', 'created_at')
    search_fields = ('text', 'ticket__title', 'author__username')
    ordering = ('-created_at',)


@admin.register(TicketStatusHistory)
class TicketStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'old_status', 'new_status', 'changed_by', 'changed_at')
    list_filter = ('new_status', 'changed_at')
    search_fields = ('ticket__title', 'comment')
    ordering = ('-changed_at',)


@admin.register(TicketAttachment)
class TicketAttachmentAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'file', 'uploaded_at')
    search_fields = ('ticket__title',)
    ordering = ('-uploaded_at',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'recipient', 'kind', 'is_read', 'created_at')
    list_filter = ('kind', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'recipient__username')
    ordering = ('-created_at',)


class SupportMessageInline(admin.TabularInline):
    model = SupportMessage
    extra = 0
    readonly_fields = ('created_at',)


@admin.register(SupportConversation)
class SupportConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'assigned_to', 'status', 'updated_at')
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('client__username', 'client__surname', 'subject')
    ordering = ('-updated_at',)
    inlines = [SupportMessageInline]


@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'author', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('text', 'author__username')
    ordering = ('-created_at',)
