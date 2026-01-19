from django.http import HttpResponse
from django.shortcuts import render
import datetime


def home(request):


    contexto = {
        'titulo': 'Página Inicial',
        'ano_corrente': datetime.datetime.now().year,
    }

    return render(request, 'home.html', contexto)