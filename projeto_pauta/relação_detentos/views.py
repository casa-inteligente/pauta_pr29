from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
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
        'P': 'Provisório',
        'F': 'Fechado',
        'SA': 'Semiaberto'
    }

    local_alocacao_map = {
        'F' : 'Fechado',
        'SA' : 'Semiaberto'
    }

    for relacao in relacoes:
        relacao.regime_nome_completo = regime_map.get(relacao.regime, relacao.regime)
        relacao.local_alocacao_nome_completo = local_alocacao_map.get(relacao.local_alocacao, relacao.local_alocacao)

    return render(request, 'relacao_list.html', {'relacoes': relacoes})
