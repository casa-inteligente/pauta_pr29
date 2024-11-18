# compromissos/views.py
from django.shortcuts import render
from .models import Compromisso
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

def listar_compromissos(request):
    compromissos = Compromisso.objects.all()
    return render(request, 'compromissos/lista.html', {'compromissos': compromissos})

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