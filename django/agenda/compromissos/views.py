# compromissos/views.py
from django.shortcuts import render, redirect
from .models import Compromisso
from django.contrib.auth.decorators import login_required
from django.utils import timezone 
from datetime import timedelta
from django.http import HttpResponse
import subprocess


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


#Para rodar scripty
def execute_script(request):
    try:
        #chama o script
        script_path = r"C:\\Users\\AULA-1\\Documents\\GitHub\\sheet_dot\\main.py"
        subprocess.call(['python', script_path])
        return HttpResponse(f'Script Retornado com sucesso')
    except Exception as e:
        return HttpResponse(f'Error as executar o Script:\t{str(e)}')