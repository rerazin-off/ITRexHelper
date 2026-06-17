from django.urls import path
from . import views

urlpatterns = [
    path('', views.ticket_list, name='ticket_list'),
    path('<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    path('create/', views.ticket_create, name='ticket_create'),
    path('<int:ticket_id>/update-status/', views.ticket_update_status, name='ticket_update_status'),
    path('<int:ticket_id>/add-comment/', views.add_comment, name='add_comment'),
]