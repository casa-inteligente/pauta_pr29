from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'pauta'

urlpatterns = [
    path('', views.index, name='index'),
    path('all/', views.pauta_all, name='pauta_all'),
    path('password_change/', auth_views.PasswordChangeView.as_view(), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
]
