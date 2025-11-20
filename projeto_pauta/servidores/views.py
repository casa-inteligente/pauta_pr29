from django.shortcuts import render, get_object_or_404, redirect
from .models import Servidores, ServidorFerias, ServidorAtestadoMedico, ServidorFolgaCompensatoria, ServidoresExtra
from django.http import HttpResponse

from projeto_pauta.permission_group import grupos_permitidos

from datetime import date, timedelta
import calendar
from collections import defaultdict

from projeto_pauta.decoradores.calcula_tempo import calcula_tempo, calcula_tempo_fun


@calcula_tempo_fun
def gerar_escala_mes(ano, mes):
    """Função auxiliar para gerar dados da escala de um mês específico"""
    # Obter o número de dias do mês
    num_dias_mes = calendar.monthrange(ano, mes)[1]
    data_inicio = date(ano, mes, 1)
    data_fim = date(ano, mes, num_dias_mes)
    
    # Lista dos plantões em ordem
    plantoes = ['A', 'B', 'C', 'D']
    
    # Nomes dos dias da semana
    dias_semana = [
        'segunda-feira', 'terça-feira', 'quarta-feira', 
        'quinta-feira', 'sexta-feira', 'sábado', 'domingo'
    ]
    
    # 1. Obter servidores por plantão (apenas ID e Nome para otimização)
    # Precisamos do ID para cruzar com as tabelas de férias/atestados
    servidores_por_plantao = defaultdict(list)
    servidores_query = Servidores.objects.filter(
        status_ativo=True
    ).values('id', 'nome_exibir', 'setor')
    
    # Mapa auxiliar: ID -> Nome (para uso rápido)
    mapa_nomes = {}
    
    for s in servidores_query:
        servidores_por_plantao[s['setor']].append(s)
        mapa_nomes[s['id']] = s['nome_exibir']
            
    # 2. Carregar Ausências (Férias e Atestados) em memória para evitar queries no loop
    # Set de tuplas (servidor_id, data)
    ausencias = set()
    
    # Buscar Férias
    ferias = ServidorFerias.objects.filter(
        inicio_ferias__lte=data_fim,
        fim_ferias__gte=data_inicio
    ).values('servidor_id', 'inicio_ferias', 'fim_ferias')
    
    for f in ferias:
        inicio = max(f['inicio_ferias'], data_inicio)
        fim = min(f['fim_ferias'], data_fim)
        curr = inicio
        while curr <= fim:
            ausencias.add((f['servidor_id'], curr))
            curr += timedelta(days=1)
            
    # Buscar Atestados
    atestados = ServidorAtestadoMedico.objects.filter(
        data_inicio__lte=data_fim,
        data_fim__gte=data_inicio
    ).values('servidor_id', 'data_inicio', 'data_fim')
    
    for a in atestados:
        inicio = max(a['data_inicio'], data_inicio)
        fim = min(a['data_fim'], data_fim)
        curr = inicio
        while curr <= fim:
            ausencias.add((a['servidor_id'], curr))
            curr += timedelta(days=1)

    # 3. Carregar Extras em memória
    # Dicionário: data -> periodo -> lista de nomes
    extras_map = defaultdict(lambda: defaultdict(list))
    
    extras_db = ServidoresExtra.objects.filter(
        data_extra__year=ano,
        data_extra__month=mes
    ).values('data_extra', 'periodo_extra', 'servidor__nome_exibir')
    
    for extra in extras_db:
        extras_map[extra['data_extra']][extra['periodo_extra']].append(extra['servidor__nome_exibir'])

    # Data de referência (01/01/2024 = Plantão A) - Ajuste conforme sua lógica
    data_referencia = date(2025, 10, 31)
    
    # Gerar dados da escala
    escala_dados = []
    
    for dia in range(1, num_dias_mes + 1):
        data_dia = date(ano, mes, dia)
        
        # Calcular plantão do dia
        dias_desde_referencia = (data_dia - data_referencia).days
        plantao_indice = dias_desde_referencia % 4
        plantao_dia = plantoes[plantao_indice]
        plantao_key = f'PLANTAO_{plantao_dia}'
        
        # Dia da semana
        dia_semana_num = data_dia.weekday()
        nome_dia_semana = dias_semana[dia_semana_num]
        
        # Filtrar servidores disponíveis (usando dados em memória)
        servidores_disponiveis = []
        lista_servidores = servidores_por_plantao.get(plantao_key, [])
        
        for servidor in lista_servidores:
            # Verifica se o par (id, data) está no set de ausências
            if (servidor['id'], data_dia) not in ausencias:
                servidores_disponiveis.append(servidor['nome_exibir'])
        
        # Obter extras do mapa em memória
        extras_dia = extras_map[data_dia]
        
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
        })
    
    return escala_dados


#@grupos_permitidos('relacao',)
@calcula_tempo
def lista_escala_servidores(request):
    """View para escala do mês atual"""
    hoje = date.today()
    escala_dados = gerar_escala_mes(hoje.year, hoje.month)
    fim_do_mes = date(hoje.year, hoje.month, calendar.monthrange(hoje.year, hoje.month)[1])
    
    
    #print(f'Fim do mes data:{fim_do_mes}')
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

    if servidores_em_ferias:
        nomes_ferias = [servidor.servidor.nome_exibir for servidor in servidores_em_ferias]
        
        #print(f'Servidores em ferias: {", ".join(nomes_ferias)}')
        #print(f'de {servidores_em_ferias[0].inicio_ferias.strftime("%d/%m/%Y")} até {servidores_em_ferias[0].fim_ferias.strftime("%d/%m/%Y")}')
    else:
        print('Nenhum servidor em ferias')

    contexto = {
        'escala_dados': escala_dados,
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


#@grupos_permitidos('relacao',)
def escala_proximo_mes(request):
    """View para escala do próximo mês"""
    hoje = date.today()
    
    if hoje.month == 12:
        proximo_ano = hoje.year + 1
        proximo_mes = 1
    else:
        proximo_ano = hoje.year
        proximo_mes = hoje.month + 1
    
    escala_dados = gerar_escala_mes(proximo_ano, proximo_mes)
    
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
        'ano_corrente': proximo_ano,
        'mes_corrente': proximo_mes,
        'nome_mes': calendar.month_name[proximo_mes],
        'mes_anterior': mes_anterior,
        'mes_proximo': mes_seguinte,
        'tipo_visualizacao': 'proximo',
        'titulo_pagina': f'{calendar.month_name[proximo_mes]} {proximo_ano}'
    }
    return render(request, 'escala_servidores.html', contexto)


#@grupos_permitidos('relacao',)
def escala_historico(request):
    """View para histórico de escalas"""
    ano = request.GET.get('ano', date.today().year)
    mes = request.GET.get('mes', date.today().month)
    
    try:
        ano = int(ano)
        mes = int(mes)
        
        # Validar mês
        if mes < 1 or mes > 12:
            mes = date.today().month
            
    except ValueError:
        ano = date.today().year
        mes = date.today().month
    
    escala_dados = gerar_escala_mes(ano, mes)
    
    # Calcular navegação
    if mes == 1:
        mes_anterior = {'ano': ano - 1, 'mes': 12}
    else:
        mes_anterior = {'ano': ano, 'mes': mes - 1}
    
    if mes == 12:
        mes_proximo = {'ano': ano + 1, 'mes': 1}
    else:
        mes_proximo = {'ano': ano, 'mes': mes + 1}
    
    # Gerar lista de anos disponíveis para o select
    ano_atual = date.today().year
    anos_disponiveis = list(range(ano_atual - 5, ano_atual + 2))
    
    contexto = {
        'escala_dados': escala_dados,
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