"""
URL configuration for projeto_pauta project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/

"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Interfaces padrões
    path('', include('pauta.urls')),
    path('relacoes/', include('relação_detentos.urls')), #adiciona relação de detentos
    path('home', views.home, name='home'),
    path('resenha_livro/', include('resenha_livro.urls')), #Adiciona relação de livros
    path('estatisticas/', include('estatisticas.urls')), #Adiciona estatísticas
    path('servidores/', include('servidores.urls')), #Adiciona servidores


    #Interfaces administrativas
    path('summernote/', include('django_summernote.urls')), #Editor de texto
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(), name='login'),  # URL de login
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),  # URL de logout
    path('accounts/', include('django.contrib.auth.urls')),  # URLs de autenticação padrão
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
