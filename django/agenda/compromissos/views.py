# compromissos/views.py
from django.shortcuts import render
from .models import Compromisso
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.utils import timezone 
from datetime import timedelta

def listar_compromissos(request): 
    hoje = timezone.now().date()
    amanha = hoje + timedelta(days=1) 
    compromissos = Compromisso.objects.filter(data__gte=hoje, data__lte=amanha)
    return render(request, 'compromissos/lista.html', {'compromissos': compromissos})

def pagina_inicial(request):
     hoje = timezone.now().date()
     amanha = hoje + timedelta(days=1)
     compromissos = Compromisso.objects.filter(data__gte=hoje, data__lte=amanha) 
     return render(request, 'compromissos/lista.html', {'compromissos': compromissos})

# Adiciona a página de ajuda
def pagina_ajuda(request):
    return render(request, 'compromissos/ajuda.html')


@login_required
def admin_compromissos(request): 
    compromissos = Compromisso.objects.all() 

    if request.method == "POST":
        data = request.POST[data]
        horario = request.POST['horario'] 
        nome = request.POST['nome'] 
        situacao = request.POST['situacao'] 
        adicionado_por = request.user

        novo_compromisso = Compromisso(data=data, horario=horario, nome=nome, situacao=situacao, adicionado_por=adicionado_por)
        novo_compromisso.save()
        return redirect('admin_compromissos')

    return render(request, 'compromissos/admin.html', {'compromissos': compromissos})