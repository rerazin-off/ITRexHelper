from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView  # ← Добавили импорт

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('users.urls')),
    path('tickets/', include('tickets.urls')),

    # Главная страница перенаправляет на список заявок
    path('', RedirectView.as_view(url='/tickets/', permanent=False)),
]

# Для работы с медиа-файлами (PDF-договоры)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)