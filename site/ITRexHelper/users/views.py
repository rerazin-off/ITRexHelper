from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_not_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .forms import CustomLoginForm, CustomRegistrationForm


@login_not_required
@require_http_methods(['GET', 'POST'])
def login_view(request):
    """
    Авторизация пользователя.
    Сценарий: ввод email и пароля → проверка в БД → вход или сообщение об ошибке.
    """
    if request.user.is_authenticated:
        return redirect('ticket_list')

    form = CustomLoginForm(request, data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        messages.success(request, 'Вы успешно вошли в систему.')
        next_url = request.GET.get('next')
        if next_url:
            return redirect(next_url)
        return redirect('ticket_list')

    return render(request, 'users/login.html', {'form': form})


@login_not_required
@require_http_methods(['GET', 'POST'])
def register_view(request):
    """
    Регистрация нового клиента.
    Сценарий: ввод данных → проверка → сохранение в БД → переход к авторизации.
    """
    if request.user.is_authenticated:
        return redirect('ticket_list')

    form = CustomRegistrationForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(
            request,
            'Регистрация прошла успешно. Войдите, используя email и пароль.',
        )
        return redirect('login')

    return render(request, 'users/register.html', {'form': form})


@require_http_methods(['GET', 'POST'])
def logout_view(request):
    """Выход из системы с перенаправлением на страницу входа."""
    logout(request)
    messages.success(request, 'Вы вышли из системы.')
    return redirect('login')
