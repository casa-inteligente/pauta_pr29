from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
import datetime
from django.utils import timezone
from .forms import TailwindPasswordChangeForm, UserProfileForm

def home(request):


    contexto = {
        'titulo': 'Página Inicial',
        'ano_corrente': timezone.now().year,
    }

    return render(request, 'home.html', contexto)


@login_required
def config_user(request):
    contexto = {
        "titulo": "Configurações do Usuário",
        "ano_corrente": timezone.now().year,
    }

    return render(request, "config_user.html", contexto)


@login_required
def config_user_dados(request):
    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=request.user)

        if form.is_valid():
            form.save()
            return render(request, "partials/config_user_dados_form.html", {
                "form": UserProfileForm(instance=request.user),
                "salvo": True,
            })
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, "partials/config_user_dados_form.html", {
        "form": form,
    })


@login_required
def config_user_senha(request):
    if request.method == "POST":
        form = TailwindPasswordChangeForm(request.user, request.POST)

        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)

            return render(request, "partials/config_user_senha_form.html", {
                "form": TailwindPasswordChangeForm(request.user),
                "salvo": True,
            })
    else:
        form = TailwindPasswordChangeForm(request.user)

    return render(request, "partials/config_user_senha_form.html", {
        "form": form,
    })