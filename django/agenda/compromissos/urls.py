# compromissos/urls.py
from django.urls import path
from . import views
from django.views.generic import TemplateView

urlpatterns = [
    path('', views.pagina_inicial, name='pagina_inicial'),
    path('admin/', views.admin_compromissos, name='admin_compromissos'),
    path('ajuda/', views.pagina_ajuda, name='pagina_ajuda'),
]
