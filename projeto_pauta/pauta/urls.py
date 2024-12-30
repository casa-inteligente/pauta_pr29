from django.urls import path
from . import views

app_name = 'pauta'

urlpatterns = [
    path('', views.index, name='index'),
    path('all/', views.pauta_all, name='pauta_all'),
]