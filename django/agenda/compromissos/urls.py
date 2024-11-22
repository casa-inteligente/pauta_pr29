# compromissos/urls.py
from django.urls import path
from . import views


urlpatterns = [
    path('', views.pagina_inicial, name='pagina_inicial'),
    path('admin/', views.admin_compromissos, name='admin_compromissos'),
    path('ajuda/', views.pagina_ajuda, name='pagina_ajuda'),
    path('execute-script/', views.execute_script, name='execute_script'),
]
