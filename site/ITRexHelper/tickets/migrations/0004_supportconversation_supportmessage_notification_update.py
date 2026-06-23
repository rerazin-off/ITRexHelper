from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def migrate_notification_data(apps, schema_editor):
    Notification = apps.get_model("tickets", "Notification")

    type_to_kind = {
        "STATUS_CHANGED": "STATUS",
        "NEW_COMMENT": "COMMENT",
        "TICKET_CREATED": "TICKET",
        "TICKET_ASSIGNED": "TICKET",
        "CHAT_MESSAGE": "CHAT",
        "APPOINTMENT": "TICKET",
    }

    type_to_title = {
        "STATUS_CHANGED": "Изменение статуса",
        "NEW_COMMENT": "Новый комментарий",
        "TICKET_CREATED": "Новая заявка",
        "TICKET_ASSIGNED": "Назначение исполнителя",
        "CHAT_MESSAGE": "Сообщение в чате",
        "APPOINTMENT": "Назначение времени",
    }

    for notification in Notification.objects.all():
        source_type = getattr(notification, "notification_type", "") or ""
        notification.kind = type_to_kind.get(source_type, "TICKET")
        notification.title = type_to_title.get(source_type, "Уведомление")
        notification.save(update_fields=["kind", "title"])


class Migration(migrations.Migration):

    dependencies = [
        ("tickets", "0003_notification"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameField(
            model_name="notification",
            old_name="user",
            new_name="recipient",
        ),
        migrations.AlterModelOptions(
            name="notification",
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddField(
            model_name="notification",
            name="actor",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="created_notifications",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="notification",
            name="kind",
            field=models.CharField(
                choices=[
                    ("TICKET", "Заявка"),
                    ("COMMENT", "Комментарий"),
                    ("STATUS", "Статус"),
                    ("CHAT", "Чат"),
                ],
                default="TICKET",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="notification",
            name="title",
            field=models.CharField(default="Уведомление", max_length=160),
            preserve_default=False,
        ),
        migrations.RunPython(migrate_notification_data, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="notification",
            name="notification_type",
        ),
        migrations.AlterField(
            model_name="notification",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name="notification",
            name="is_read",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="notification",
            name="message",
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name="notification",
            name="recipient",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="notifications",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="notification",
            name="ticket",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="notifications",
                to="tickets.ticket",
            ),
        ),
        migrations.CreateModel(
            name="SupportConversation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("subject", models.CharField(default="Чат поддержки", max_length=180)),
                ("status", models.CharField(choices=[("OPEN", "Открыт"), ("WAITING_CLIENT", "Ожидает клиента"), ("RESOLVED", "Решен")], default="OPEN", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("assigned_to", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="assigned_support_conversations", to=settings.AUTH_USER_MODEL)),
                ("client", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="support_conversations", to=settings.AUTH_USER_MODEL)),
                ("ticket", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="support_conversations", to="tickets.ticket")),
            ],
            options={"ordering": ["-updated_at"]},
        ),
        migrations.CreateModel(
            name="SupportMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("text", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("author", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="support_messages", to=settings.AUTH_USER_MODEL)),
                ("conversation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="tickets.supportconversation")),
            ],
            options={"ordering": ["created_at"]},
        ),
    ]
