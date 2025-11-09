from django.shortcuts import render, get_object_or_404, redirect
from .models import Servidores, ServidorFerias, ServidorAtestadoMedico, ServidorFolgaCompensatoria, ServidoresExtra
from django.http import HttpResponse

from projeto_pauta.permission_group import grupos_permitidos

from datetime import date, timedelta
import calendar


def gerar_escala_mes(ano, mes):
    """Função auxiliar para gerar dados da escala de um mês específico"""
    # Obter o número de dias do mês
    num_dias_mes = calendar.monthrange(ano, mes)[1]
    
    # Lista dos plantões em ordem
    plantoes = ['A', 'B', 'C', 'D']
    
    # Nomes dos dias da semana
    dias_semana = [
        'segunda-feira', 'terça-feira', 'quarta-feira', 
        'quinta-feira', 'sexta-feira', 'sábado', 'domingo'
    ]
    
    # Obter servidores por plantão (ativos)
    servidores_por_plantao = {}
    for plantao in ['PLANTAO_A', 'PLANTAO_B', 'PLANTAO_C', 'PLANTAO_D']:
        servidores_por_plantao[plantao] = Servidores.objects.filter(
            setor=plantao,
            status_ativo=True
        )
    
    # Data de referência para calcular sequência contínua (01/01/2024 = Plantão A)
    data_referencia = date(2025, 10, 31)  # Esta data será plantão A
    
    # Gerar dados da escala
    escala_dados = []
    
    for dia in range(1, num_dias_mes + 1):
        data_dia = date(ano, mes, dia)
        
        # Calcular quantos dias se passaram desde a data de referência
        dias_desde_referencia = (data_dia - data_referencia).days
        
        # Determinar o plantão baseado na sequência contínua A,B,C,D
        plantao_indice = dias_desde_referencia % 4
        plantao_dia = plantoes[plantao_indice]
        plantao_key = f'PLANTAO_{plantao_dia}'
        
        # Obter dia da semana
        dia_semana_num = data_dia.weekday()  # 0=segunda, 6=domingo
        nome_dia_semana = dias_semana[dia_semana_num]
        
        # Servidores do plantão que estão disponíveis
        servidores_disponiveis = []
        for servidor in servidores_por_plantao.get(plantao_key, []):
            # Verificar se não está de férias
            em_ferias = ServidorFerias.objects.filter(
                servidor=servidor,
                inicio_ferias__lte=data_dia,
                fim_ferias__gte=data_dia
            ).exists()
            
            # Verificar se não está com atestado
            com_atestado = ServidorAtestadoMedico.objects.filter(
                servidor=servidor,
                data_inicio__lte=data_dia,
                data_fim__gte=data_dia
            ).exists()
            
            # Verificar se não está de folga compensatória
            de_folga = ServidorFolgaCompensatoria.objects.filter(
                servidor=servidor,
                data_folga=data_dia
            ).exists()
            
            if not (em_ferias or com_atestado or de_folga):
                servidores_disponiveis.append(servidor.nome_exibir)
        
        # Obter extras por horário - usando nome_exibir
        extras_primeiro = list(ServidoresExtra.objects.filter(
            data_extra=data_dia,
            periodo_extra='PRIMEIRO_HORARIO'
        ).values_list('servidor__nome_exibir', flat=True))
        
        extras_segundo = list(ServidoresExtra.objects.filter(
            data_extra=data_dia,
            periodo_extra='SEGUNDO_HORARIO'
        ).values_list('servidor__nome_exibir', flat=True))
        
        extras_terceiro = list(ServidoresExtra.objects.filter(
            data_extra=data_dia,
            periodo_extra='TERCEIRO_HORARIO'
        ).values_list('servidor__nome_exibir', flat=True))
        
        escala_dados.append({
            'dia': dia,
            'nome_dia_semana': nome_dia_semana,
            'plantao': plantao_dia,
            'servidores_lista': servidores_disponiveis,
            'servidores': ', '.join(servidores_disponiveis),
            'extras_primeiro_lista': extras_primeiro,
            'extras_primeiro': ', '.join(extras_primeiro),
            'extras_segundo_lista': extras_segundo,
            'extras_segundo': ', '.join(extras_segundo),
            'extras_terceiro_lista': extras_terceiro,
            'extras_terceiro': ', '.join(extras_terceiro),
            'data': data_dia,
        })
    
    return escala_dados


#@grupos_permitidos('relacao',)
def lista_escala_servidores(request):
    """View para escala do mês atual"""
    hoje = date.today()
    escala_dados = gerar_escala_mes(hoje.year, hoje.month)
    
    # Calcular mês anterior e próximo para navegação
    if hoje.month == 1:
        mes_anterior = {'ano': hoje.year - 1, 'mes': 12}
    else:
        mes_anterior = {'ano': hoje.year, 'mes': hoje.month - 1}
    
    if hoje.month == 12:
        mes_proximo = {'ano': hoje.year + 1, 'mes': 1}
    else:
        mes_proximo = {'ano': hoje.year, 'mes': hoje.month + 1}
    
    contexto = {
        'escala_dados': escala_dados,
        'ano_corrente': hoje.year,
        'mes_corrente': hoje.month,
        'nome_mes': calendar.month_name[hoje.month],
        'mes_anterior': mes_anterior,
        'mes_proximo': mes_proximo,
        'tipo_visualizacao': 'atual',
        'titulo_pagina': f'Escala {calendar.month_name[hoje.month]}'
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