from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from .models import Relacao
from django.db.models import Case, When, Value
from django.db.models.functions import Concat

@login_required
def relacao_list(request):
    regime_order = Case(
        When(regime='P', then=Value(1)),
        When(regime='F', then=Value(2)),
        When(regime='SA', then=Value(3)),
    )

    relacoes = Relacao.objects.all().annotate(
        regime_order=regime_order
    ).order_by('regime_order', 'previsao_saida', 'local_alocacao', 'nome')

    regime_map = {
        'PRO': 'Provisório',
        'F': 'Fechado',
        'SA': 'Semiaberto',
        'TOR': 'Tornozeleira',
        'PRE': 'Preventiva',
        'A' : 'Alimentos'
    }

    local_alocacao_map = {
        'F' : 'Fechado',
        'SA' : 'Semiaberto',
        'TOR' : 'Domiciliar'
    }

    for relacao in relacoes:
        relacao.regime_nome_completo = regime_map.get(relacao.regime, relacao.regime)
        relacao.local_alocacao_nome_completo = local_alocacao_map.get(relacao.local_alocacao, relacao.local_alocacao)

    return render(request, 'relacao_list.html', {
        'relacoes': relacoes,
        'csrf_token': request.COOKIES.get('csrftoken', '')  # Adiciona o CSRF token ao contexto
    })

@csrf_exempt
def salvar_alteracoes(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            for item in data:
                detento = Relacao.objects.get(id=item['id'])
                for field, value in item.items():
                    if field != 'id' and hasattr(detento, field):
                        setattr(detento, field, value)
                detento.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Método não permitido'})