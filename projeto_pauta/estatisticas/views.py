from django.shortcuts import render
from django.db.models import Count
from relação_detentos.models import Relacao

def estatisticas_view(request):
    artigos = (
        Relacao.objects
        .values('artigo')
        .annotate(quantidade=Count('id'))
        .order_by('artigo')
    )
    comarcas = (
        Relacao.objects
        .values('comarca')
        .annotate(quantidade=Count('id'))
        .order_by('comarca')
    )
    regimes = (
        Relacao.objects
        .values('regime')
        .annotate(quantidade=Count('id'))
        .order_by('regime')
    )
    regimes = [
        {'regime': item['regime'] if item['regime'] is not None else 'Não informado', 'quantidade': item['quantidade']}
        for item in regimes
    ]
    alocacoes = (
        Relacao.objects
        .values('local_alocacao')
        .annotate(quantidade=Count('id'))
        .order_by('local_alocacao')
    )
    data_atualizado = Relacao.objects.latest('atualizado').atualizado if Relacao.objects.exists() else None

    contexto = {
        'titulo': 'Estatísticas',
        'nome_unidade': 'Presídio Regional de Maravilha',
        'artigos': list(artigos),
        'comarcas': list(comarcas),
        'regimes': list(regimes),
        'alocacoes': list(alocacoes),
        'data_atualizado': data_atualizado,
    }
    return render(request, 'estatisticas.html', contexto)