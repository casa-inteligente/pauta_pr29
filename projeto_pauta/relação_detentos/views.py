from django.shortcuts import render
from .models import Relacao
from django.db.models import Case, When, Value
from django.db.models.functions import Concat

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

    return render(request, 'relacao_list.html', {'relacoes': relacoes})
