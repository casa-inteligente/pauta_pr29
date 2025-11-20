from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

app_name = 'pauta'

urlpatterns = [
    path('', views.pauta_all, name='pauta_all'),
    path('all/', views.index, name='index'), #utilizado para visualização na aréa de trabalho
    path('all/7', views.index_7, name='index_7'),

    
    path('password_change/', auth_views.PasswordChangeView.as_view(), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
   
   # APIs REST
    path('api/4dias/', views.api_pauta_4dias, name='api_pauta_4dias'),
    path('api/data/', views.api_pauta_por_data, name='api_pauta_por_data'),

    # Visualizador da API
    path('api/viewer/', views.pauta_api_viewer, name='api_viewer'),
]
