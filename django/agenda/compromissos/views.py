from django.shortcuts import render
from .models import Compromisso

# Create your views here.

def listar_compromissos(request):
    compromissos = Compromisso.objects.all()
    return render(request, "compromissos/admin.html", {'compromissos': compromissos})
