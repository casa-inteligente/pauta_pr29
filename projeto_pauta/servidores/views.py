from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponse

from .models import Servidores, ServidorFerias, ServidorAtestadoMedico, ServidorFolgaCompensatoria, ServidoresExtra
from projeto_pauta.permission_group import grupos_permitidos

from datetime import date, timedelta
import calendar
from collections import defaultdict
import logging

from projeto_pauta.decoradores.calcula_tempo import calcula_tempo, calcula_tempo_fun


logger = logging.getLogger(__name__)

if settings.DEBUG:
    from projeto_pauta.decoradores.calcula_tempo import calcula_tempo, calcula_tempo_fun
    checked_debug_decorador = calcula_tempo
    checked_debug_decorador_fun = calcula_tempo_fun
    checked_login_required = lambda x: x
    print_debug = True
else:
    print_debug = False
    checked_login_required = login_required
    checked_debug_decorador = lambda x: x
    checked_debug_decorador_fun = lambda x: x  # Decorador vazio



@checked_login_required
@checked_debug_decorador_fun
def gerar_escala_mes(ano, mes):
    """Função auxiliar para gerar dados da escala de um mês específico"""
    num_dias_mes = calendar.monthrange(ano, mes)[1]
    data_inicio = date(ano, mes, 1)
    data_fim = date(ano, mes, num_dias_mes)
    
    plantoes = ['A', 'B', 'C', 'D']
    dias_semana = [
        'segunda-feira', 'terça-feira', 'quarta-feira', 
        'quinta-feira', 'sexta-feira', 'sábado', 'domingo'
    ]
    
    # 1. Carregar servidores
    servidores_por_plantao = defaultdict(list)
    servidores_query = Servidores.objects.filter(status_ativo=True).values('id', 'nome_exibir', 'setor')
    mapa_id_para_nome = {}
    
    for s in servidores_query:
        servidores_por_plantao[s['setor']].append(s)
        mapa_id_para_nome[s['id']] = s['nome_exibir']
    
    # 2. Carregar ausências COM OS PERÍODOS
    # Dicionário: data -> {'ferias': {chave: dados}, 'atestados': {}, 'folgas': {}}
    ausencias_por_tipo = defaultdict(lambda: {'ferias': {}, 'atestados': {}, 'folgas': {}})
    ausencias_ids = set()  # Para filtrar da escala principal
    
    # Férias
    ferias = ServidorFerias.objects.filter(
        inicio_ferias__lte=data_fim,
        fim_ferias__gte=data_inicio
    ).values('servidor_id', 'inicio_ferias', 'fim_ferias')
    
    for f in ferias:
        inicio = max(f['inicio_ferias'], data_inicio)
        fim = min(f['fim_ferias'], data_fim)
        curr = inicio
        nome_servidor = mapa_id_para_nome.get(f['servidor_id'], 'Desconhecido')
        
        while curr <= fim:
            ausencias_ids.add((f['servidor_id'], curr))
            # Armazena com chave única para evitar duplicatas
            chave = f"{f['servidor_id']}_{f['inicio_ferias']}_{f['fim_ferias']}"
            ausencias_por_tipo[curr]['ferias'][chave] = {
                'nome': nome_servidor,
                'inicio': f['inicio_ferias'],
                'fim': f['fim_ferias']
            }
            curr += timedelta(days=1)
    
    # Atestados
    atestados = ServidorAtestadoMedico.objects.filter(
        data_inicio__lte=data_fim,
        data_fim__gte=data_inicio
    ).values('servidor_id', 'data_inicio', 'data_fim')
    
    for a in atestados:
        inicio = max(a['data_inicio'], data_inicio)
        fim = min(a['data_fim'], data_fim)
        curr = inicio
        nome_servidor = mapa_id_para_nome.get(a['servidor_id'], 'Desconhecido')
        
        while curr <= fim:
            ausencias_ids.add((a['servidor_id'], curr))
            chave = f"{a['servidor_id']}_{a['data_inicio']}_{a['data_fim']}"
            ausencias_por_tipo[curr]['atestados'][chave] = {
                'nome': nome_servidor,
                'inicio': a['data_inicio'],
                'fim': a['data_fim']
            }
            curr += timedelta(days=1)
    
    # Folgas Compensatórias (são pontuais, apenas um dia)
    folgas = ServidorFolgaCompensatoria.objects.filter(
        data_folga__year=ano,
        data_folga__month=mes
    ).values('servidor_id', 'data_folga')
    
    for folga in folgas:
        ausencias_ids.add((folga['servidor_id'], folga['data_folga']))
        nome_servidor = mapa_id_para_nome.get(folga['servidor_id'], 'Desconhecido')
        chave = f"{folga['servidor_id']}_{folga['data_folga']}"
        ausencias_por_tipo[folga['data_folga']]['folgas'][chave] = {
            'nome': nome_servidor,
            'data': folga['data_folga']
        }

    # 3. Carregar Extras
    extras_map = defaultdict(lambda: defaultdict(list))
    extras_db = ServidoresExtra.objects.filter(
        data_extra__year=ano,
        data_extra__month=mes
    ).values('data_extra', 'periodo_extra', 'servidor__nome_exibir')
    
    for extra in extras_db:
        extras_map[extra['data_extra']][extra['periodo_extra']].append(extra['servidor__nome_exibir'])
        if print_debug:
            print('+'*60)
            print(f"Extra carregado: {extra['data_extra']} - {extra['periodo_extra']} - {extra['servidor__nome_exibir']}")

    data_referencia = date(2025, 10, 31)
    escala_dados = []
    
    # 4. Gerar dados para cada dia do mês
    for dia in range(1, num_dias_mes + 1):
        data_dia = date(ano, mes, dia)
        
        dias_desde_referencia = (data_dia - data_referencia).days
        plantao_indice = dias_desde_referencia % 4
        plantao_dia = plantoes[plantao_indice]
        plantao_key = f'PLANTAO_{plantao_dia}'
        
        dia_semana_num = data_dia.weekday()
        nome_dia_semana = dias_semana[dia_semana_num]
        
        # Servidores disponíveis
        servidores_disponiveis = []
        lista_servidores = servidores_por_plantao.get(plantao_key, [])
        
        for servidor in lista_servidores:
            if (servidor['id'], data_dia) not in ausencias_ids:
                servidores_disponiveis.append(servidor['nome_exibir'])
        
        # Obter extras e ausências do dia
        extras_dia = extras_map[data_dia]
        ausencias_dia = ausencias_por_tipo[data_dia]
        
        escala_dados.append({
            'dia': dia,
            'nome_dia_semana': nome_dia_semana,
            'plantao': plantao_dia,
            'servidores_lista': servidores_disponiveis,
            'servidores': ', '.join(servidores_disponiveis),
            'extras_primeiro_lista': extras_dia['PRIMEIRO_HORARIO'],
            'extras_primeiro': ', '.join(extras_dia['PRIMEIRO_HORARIO']),
            'extras_segundo_lista': extras_dia['SEGUNDO_HORARIO'],
            'extras_segundo': ', '.join(extras_dia['SEGUNDO_HORARIO']),
            'extras_terceiro_lista': extras_dia['TERCEIRO_HORARIO'],
            'extras_terceiro': ', '.join(extras_dia['TERCEIRO_HORARIO']),
            'data': data_dia,
            # Ausências com períodos (convertendo dict para list)
            'ferias_dict': ausencias_dia['ferias'],
            'atestados_dict': ausencias_dia['atestados'],
            'folgas_dict': ausencias_dia['folgas'],
        })
    
    # 5. Consolidar TODAS as ausências únicas do mês (para sidebar)
    todas_ferias = {}
    todas_atestados = {}
    todas_folgas = {}
    
    for dia_dados in escala_dados:
        # Férias
        for chave, dados in dia_dados.get('ferias_dict', {}).items():
            todas_ferias[chave] = dados
        # Atestados
        for chave, dados in dia_dados.get('atestados_dict', {}).items():
            todas_atestados[chave] = dados
        # Folgas
        for chave, dados in dia_dados.get('folgas_dict', {}).items():
            todas_folgas[chave] = dados
    
    # Retorna dados da escala E o dicionário consolidado de ausências
    return escala_dados, {
        'ferias': list(todas_ferias.values()),
        'atestados': list(todas_atestados.values()),
        'folgas': list(todas_folgas.values())
    }



@checked_debug_decorador
@checked_login_required
def lista_escala_servidores(request):
    """View para escala do mês atual"""
    hoje = date.today()
    escala_dados, todas_ausencias = gerar_escala_mes(hoje.year, hoje.month)  # <-- MUDOU AQUI
    fim_do_mes = date(hoje.year, hoje.month, calendar.monthrange(hoje.year, hoje.month)[1])
    
    # Calcular mês anterior e próximo para navegação
    if hoje.month == 1:
        mes_anterior = {'ano': hoje.year - 1, 'mes': 12}
    else:
        mes_anterior = {'ano': hoje.year, 'mes': hoje.month - 1}
    
    if hoje.month == 12:
        mes_proximo = {'ano': hoje.year + 1, 'mes': 1}
    else:
        mes_proximo = {'ano': hoje.year, 'mes': hoje.month + 1}
    
    servidores_em_ferias = ServidorFerias.objects.filter(
        inicio_ferias__lte=hoje,
        fim_ferias__gte=fim_do_mes
    ).select_related('servidor')

    contexto = {
        'escala_dados': escala_dados,
        'todas_ausencias': todas_ausencias,  # <-- ADICIONE ESTA LINHA
        'ano_corrente': hoje.year,
        'mes_corrente': hoje.month,
        'nome_mes': calendar.month_name[hoje.month],
        'mes_anterior': mes_anterior,
        'mes_proximo': mes_proximo,
        'tipo_visualizacao': 'atual',
        'titulo_pagina': f'Escala {calendar.month_name[hoje.month]}',
        'servidores_em_ferias': servidores_em_ferias,
    }
    return render(request, 'escala_servidores.html', contexto)


@checked_debug_decorador
@checked_login_required
def escala_proximo_mes(request):
    """View para escala do próximo mês"""
    hoje = date.today()
    
    if hoje.month == 12:
        proximo_ano = hoje.year + 1
        proximo_mes = 1
    else:
        proximo_ano = hoje.year
        proximo_mes = hoje.month + 1
    
    escala_dados, todas_ausencias = gerar_escala_mes(proximo_ano, proximo_mes)  # <-- MUDOU AQUI
    
    # Calcular navegação
    if proximo_mes == 1:
        mes_anterior = {'ano': proximo_ano - 1, 'mes': 12}
    else:
        mes_anterior = {'ano': proximo_ano, 'mes': proximo_mes - 1}
    
    if proximo_mes == 12:
        mes_seguinte = {'ano': proximo_ano + 1, 'mes': 1}
    else:
        mes_seguinte = {'ano': proximo_ano, 'mes': proximo_mes + 1}
    
    contexto = {
        'escala_dados': escala_dados,
        'todas_ausencias': todas_ausencias,  # <-- ADICIONE ESTA LINHA
        'ano_corrente': proximo_ano,
        'mes_corrente': proximo_mes,
        'nome_mes': calendar.month_name[proximo_mes],
        'mes_anterior': mes_anterior,
        'mes_proximo': mes_seguinte,
        'tipo_visualizacao': 'proximo',
        'titulo_pagina': f'{calendar.month_name[proximo_mes]} {proximo_ano}'
    }
    return render(request, 'escala_servidores.html', contexto)


@checked_debug_decorador
def escala_historico(request):
    """View para histórico de escalas"""
    ano = request.GET.get('ano', date.today().year)
    mes = request.GET.get('mes', date.today().month)
    
    try:
        ano = int(ano)
        mes = int(mes)
        if mes < 1 or mes > 12:
            mes = date.today().month
    except ValueError:
        ano = date.today().year
        mes = date.today().month
    
    escala_dados, todas_ausencias = gerar_escala_mes(ano, mes)  # <-- MUDOU AQUI
    
    # Calcular navegação
    if mes == 1:
        mes_anterior = {'ano': ano - 1, 'mes': 12}
    else:
        mes_anterior = {'ano': ano, 'mes': mes - 1}
    
    if mes == 12:
        mes_proximo = {'ano': ano + 1, 'mes': 1}
    else:
        mes_proximo = {'ano': ano, 'mes': mes + 1}
    
    ano_atual = date.today().year
    anos_disponiveis = list(range(ano_atual - 5, ano_atual + 2))
    
    contexto = {
        'escala_dados': escala_dados,
        'todas_ausencias': todas_ausencias,  # <-- ADICIONE ESTA LINHA
        'ano_corrente': ano,
        'mes_corrente': mes,
        'nome_mes': calendar.month_name[mes],
        'mes_anterior': mes_anterior,
        'mes_proximo': mes_proximo,
        'anos_disponiveis': anos_disponiveis,
        'meses_disponiveis': [
            (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'),
            (4, 'Abril'), (5, 'Maio'), (6, 'Junho'),
            (7, 'Julho'), (8, 'Agosto'), (9, 'Setembro'),
            (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
        ],
        'tipo_visualizacao': 'historico',
        'titulo_pagina': f'Histórico - {calendar.month_name[mes]} {ano}'
    }
    return render(request, 'escala_servidores.html', contexto)