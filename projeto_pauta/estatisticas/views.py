from django.shortcuts import render
from django.db.models import Count
from relação_detentos.models import Relacao
from collections import defaultdict


def estatisticas_view(request):
    #Busca quantidades de Internos
    qtd_fechado = Relacao.objects.filter(local_alocacao='F').count()
    qtd_semiaberto = Relacao.objects.filter(local_alocacao='SA').count()
    total_internos = qtd_fechado + qtd_semiaberto
    qtd_preventiva = Relacao.objects.filter(regime='PRE').count()
    # Artigos: separa, limpa, soma e trata vazios
    artigos_qsRE = (
        Relacao.objects
        .values('artigo')
        .annotate(quantidade=Count('id'))
        .order_by('artigo')
    )
    artigos_dictRE = defaultdict(int)
    for item in artigos_qsRE:
        artigos_strE = (item['artigo'] or '').replace('\n', ' ')
        artigos_splitRE = [a.strip() for a in artigos_strE.split(',')]
        for artigo in artigos_splitRE:
            artigo_final = artigo if artigo else 'Não informada'
            artigos_dictRE[artigo_final] += item['quantidade']
    #artigosRE = [{'artigo': k, 'quantidade': v} for k, v in artigos_dictRE.items()]
    artigosRE = [{'artigo': k, 'quantidade': v} for k, v in artigos_dictRE.items() if k and k.strip() not in ['Não informada', '', None]]


    # você já tinha esse queryset
    artigos_qs = (
        Relacao.objects
           .values('artigo')           # string com vírgulas
           .annotate(quantidade=Count('id'))
           .order_by('artigo')
    )

    artigos_dict = defaultdict(int)


    for item in artigos_qs:
        # 1. normaliza a string (troca \n por espaço)
        artigos_str = (item['artigo'] or '').replace('\n', ' ')

        # 2. cria um SET para garantir unicidade **dentro da mesma linha**
        codigos_unicos = {
            codigo.strip() or 'Não Informado'   # <-- parênteses!
            for codigo in artigos_str.split(',')
            if codigo.strip()                   # <-- parênteses!
        } or {'Não Informado'}                  # se estava totalmente vazio

        # 3. acrescenta a quantidade só UMA VEZ por código
        for codigo in codigos_unicos:
            artigos_dict[codigo] += item['quantidade']

    # 4. transforma em lista de dicionários
    artigos = [
        {'artigo': codigo, 'quantidade': qtd}
        for codigo, qtd in artigos_dict.items()
    ]



    # Comarcas: trata vazios e None
    comarcas_qs = (
        Relacao.objects
        .values('comarca')
        .annotate(quantidade=Count('id'))
        .order_by('comarca')
    )
    comarcas = []
    for item in comarcas_qs:
        comarca = item['comarca']
        if not comarca or comarca.lower() == 'null':
            comarca = 'Não informada'
        comarcas.append({'comarca': comarca, 'quantidade': item['quantidade']})

    # Regimes: soma duplicados, trata vazios e unifica 'F', 'FECHADO', 'PRE', 'PROVISÓRIO'
    regimes_qs = (
        Relacao.objects
        .values('regime')
        .annotate(quantidade=Count('id'))
        .order_by('regime')
    )
    regimes_dict = defaultdict(int)
    for item in regimes_qs:
        regime = item['regime'] if item['regime'] else 'PROVISÓRIO'
        regime_upper = regime.strip().upper()
        # Unifica 'F' e 'FECHADO'
        if regime_upper in ['F', 'FECHADO']:
            regime = 'FECHADO'
        # Unifica 'PRE' e 'PROVISÓRIO'
        elif regime_upper in ['PRE', 'PROVISÓRIO']:
            regime = 'PROVISÓRIO'
        regimes_dict[regime] += item['quantidade']
    regimes = [{'regime': k, 'quantidade': v} for k, v in regimes_dict.items()]

    # Alocações
    alocacoes = (
        Relacao.objects
        .values('local_alocacao')
        .annotate(quantidade=Count('id'))
        .order_by('local_alocacao')
    )

    data_atualizado = Relacao.objects.latest('atualizado').atualizado if Relacao.objects.exists() else None

    # print(f'Variavel artigosRE: {artigosRE}')
    # print("--------------------------------")
    # print(F'Variavel artigo: {artigos}')

    artigosRE = sorted(artigosRE, key=lambda x: x['artigo'])
    artigos = sorted(artigos, key=lambda x: x['artigo'])
    contexto = {
        'titulo': 'Estatísticas',
        'nome_unidade': 'Presídio Regional de Maravilha',
        'artigosRE': list(artigosRE),
        'artigos': artigos,
        'comarcas': list(comarcas),
        'regimes': list(regimes),
        'alocacoes': list(alocacoes),
        'data_atualizado': data_atualizado,
        'total_internos': total_internos,
        'qtd_fechado': qtd_fechado,
        'qtd_semiaberto': qtd_semiaberto,
        'user': request.user,
    }
    return render(request, 'estatisticas.html', contexto)