# compromissos/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.pagina_inicial, name='pagina_inicial'),
    #path('', views.listar_compromissos, name='listar_compromissos'),
    path('admin/', views.admin_compromissos, name='admin_compromissos'),
]
