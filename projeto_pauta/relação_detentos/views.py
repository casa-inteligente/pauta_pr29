from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from .models import Relacao
from django.db.models import Case, When, Value
from django.db.models.functions import Concat
import datetime

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
    #cria a variavel para passar a aquantidade de presos no fechado
    qtd_fechado = relacoes.filter(local_alocacao='F').count()
    qtd_semiaberto = relacoes.filter(local_alocacao='SA').count()
    qtd_total = qtd_fechado + qtd_semiaberto
    #print(qtd_fechado)

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
        'csrf_token': request.COOKIES.get('csrftoken', ''),  # Adiciona o CSRF token ao contexto
        'qtd_fechado' : qtd_fechado, #quantidade de alocados no fechado
        'qtd_semiaberto': qtd_semiaberto, #Quantidade de alocados no semiaberto
        'qtd_total': qtd_total, #quantidade de alocados na unidade
    })

@csrf_exempt
def salvar_alteracoes(request):
    if request.method == 'POST':
        try:
            dados = json.loads(request.body)
            for item in dados:
                id = item.get('id')
                detento = Relacao.objects.get(id=id)
                detento.IPEN = item.get('IPEN')
                detento.nome = item.get('nome')
                detento.comarca = item.get('comarca')
                detento.artigo = item.get('artigo')
                detento.local_alocacao = item.get('local_alocacao')
                detento.ingresso = datetime.datetime.strptime(item.get('ingresso'), '%Y-%m-%d').date()
                detento.regime = item.get('regime')
                
                # Verificar se os campos opcionais possuem valor antes de salvar
                if item.get('pena'):
                    detento.pena = item.get('pena')
                else:
                    detento.pena = '-'
                
                # Verificar se 'previsao_saida' está presente e é uma data válida
                previsao_saida_str = item.get('previsao_saida')
                if previsao_saida_str:
                    try:
                        detento.previsao_saida = datetime.datetime.strptime(previsao_saida_str, '%Y-%m-%d').date()
                    except ValueError:
                        detento.previsao_saida = None
                else:
                    detento.previsao_saida = None
                
                # Verificar se 'atualizado' está presente e é uma data válida
                atualizado_str = item.get('atualizado')
                if atualizado_str:
                    try:
                        detento.atualizado = datetime.datetime.strptime(atualizado_str, '%Y-%m-%d').date()
                    except ValueError:
                        detento.atualizado = None
                else:
                    detento.atualizado = None
                
                detento.save()  # Salva as alterações no banco de dados
            return JsonResponse({'success': True})
        except ValueError as e:
            return JsonResponse({'success': False, 'error': f'Erro de formatação de data: {str(e)}'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Método não permitido'})