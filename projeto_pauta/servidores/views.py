import os
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.utils import timezone

from io import BytesIO
import re
import pdfplumber
import zipfile
from pypdf import PdfReader, PdfWriter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.pdfgen import canvas


from .models import Servidores, ServidorFerias, ServidorAtestadoMedico, ServidorFolgaCompensatoria, ServidoresExtra, ServidoresPlantao, UnidadeOficio
from projeto_pauta.permission_group import grupos_permitidos

import requests as http_requests
from datetime import date, timedelta
import calendar
import random
from collections import defaultdict
import logging

from projeto_pauta.decoradores.calcula_tempo import calcula_tempo, calcula_tempo_fun


logger = logging.getLogger(__name__)

if settings.DEBUG:
    from projeto_pauta.decoradores.calcula_tempo import calcula_tempo, calcula_tempo_fun
    from django.db import connection
    print(f'Banco de dados em uso:\t\t{connection.vendor}\n')
    checked_debug_decorador = calcula_tempo
    checked_debug_decorador_fun = calcula_tempo_fun
    checked_login_required = lambda x: x
    print_debug = True
else:
    print_debug = False
    checked_login_required = login_required
    checked_debug_decorador = lambda x: x
    checked_debug_decorador_fun = lambda x: x

ano_corrente = timezone.now().year
mes_corrente = timezone.now().month

# Registre Arial e Arial-Bold (se quiser usar negrito)
# Registre Arial e Arial-Bold (se quiser usar negrito)
# Caminhos relativos à pasta base do projeto
arial_path = os.path.join(settings.BASE_DIR, 'staticfiles', 'fonts', 'arial.ttf')
arial_bold_path = os.path.join(settings.BASE_DIR, 'staticfiles', 'fonts', 'arialbd.ttf')

# Registra as fontes
pdfmetrics.registerFont(TTFont('Arial', arial_path))
pdfmetrics.registerFont(TTFont('Arial-Bold', arial_bold_path))


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
    
    try:
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
    except Exception as e:
        if print_debug:
            print('Erro ao carregar férias:', e)
        ferias = []

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
    ).values('servidor_id', 'data_folga', 'observacao_folga')
    
    for folga in folgas:
        ausencias_ids.add((folga['servidor_id'], folga['data_folga']))
        nome_servidor = mapa_id_para_nome.get(folga['servidor_id'], 'Desconhecido')
        chave = f"{folga['servidor_id']}_{folga['data_folga']}"
        ausencias_por_tipo[folga['data_folga']]['folgas'][chave] = {
            'nome': nome_servidor,
            'data': folga['data_folga'],
            'observacao_folga': folga.get('observacao_folga', '')
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
    
    escala_dados, todas_ausencias = gerar_escala_mes(hoje.year, hoje.month)
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
        'todas_ausencias': todas_ausencias,  
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
    
    escala_dados, todas_ausencias = gerar_escala_mes(proximo_ano, proximo_mes) 
    
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
        'todas_ausencias': todas_ausencias,  
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
    
    escala_dados, todas_ausencias = gerar_escala_mes(ano, mes) 
    
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
        'todas_ausencias': todas_ausencias, 
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


@checked_debug_decorador
def folha_ponto(request):
    """View para exibir a folha de ponto dos servidores"""
    
    hoje = date.today()
    ano = int(request.GET.get('ano', hoje.year))
    mes = int(request.GET.get('mes', hoje.month))
    
    # Validação de mês
    if mes < 1 or mes > 12:
        mes = hoje.month
    
    self_servidores_ativos = Servidores.objects.filter(
        status_ativo=True
    ).exclude(setor='OUTRAS').order_by('setor', 'nome_exibir')
    
    if print_debug:
        print('-'*60)
        print(f'Folha de Ponto - Ano: {ano}, Mês: {mes}, Servidores Ativos: {self_servidores_ativos.count()}')
    
    contexto = {
        'user': request.user,
        'servidores_ativos': self_servidores_ativos,
        'ano_corrente': ano,
        'mes_corrente': mes,
        'titulo_pagina': 'Folha Ponto dos Servidores',
    }
    
    return render(request, 'folha_ponto.html', contexto)

def todas_folhas_ponto(request, mes, ano):
    """View para exibir todas as folhas de ponto dos servidores"""
    
    try:
        ano = int(ano)
        mes = int(mes)
        if mes < 1 or mes > 12:
            mes = date.today().month
            ano = date.today().year
    except (ValueError, TypeError):
        ano = date.today().year
        mes = date.today().month
    
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="folha_ponto_todos_{mes}.pdf"'

    pdf = canvas.Canvas(response, pagesize=A4)
    pdf.setAuthor('OgliTech')
    pdf.setLineWidth(0.5) # Espessura da linha
    pdf.setStrokeColorRGB(0, 0, 0, 0.7) #Cor da linha
    largura, altura = A4

    self_servidores_ativos = Servidores.objects.filter(
        status_ativo=True
    ).exclude(setor='OUTRAS').order_by('setor', 'nome_exibir')

    for servidor in self_servidores_ativos:
        pdf.drawImage(
            os.path.join(settings.BASE_DIR, 'staticfiles', 'servidores','img', 'logo.png'),
            0.4 * cm,
            27.8 * cm,
            width=1.5 * cm,
            height=1.5 * cm,
        )
        pdf.setFont("Arial-Bold", 10)
        pdf.drawString(2 * cm, 28.9 * cm, "ESTADO DE SANTA CATARINA")
        pdf.drawString(16.5 * cm, 29 * cm, "CONTROLE DE PONTO")
        pdf.setFont("Arial", 8)
        pdf.drawString(16 * cm, 28.3 * cm, "MÊS/ANO")
        pdf.setFont("Arial", 9)
        pdf.drawString(
            16 * cm, 27.6 * cm, f"{mes}/{ano}"
        )
        pdf.rect(
            15.9 * cm, 27.3 * cm, 4.7 * cm, 1.4 * cm, fill=0
        )
        pdf.setFont("Arial", 8)
        pdf.drawString(16 * cm, 26.9 * cm, "LOTAÇÃO (SIGLA)")
        pdf.setFont("Arial", 10)
        pdf.drawString(
            16.3 * cm, 26 * cm, "UPA20"
        )
        pdf.rect(
            15.9 * cm, 25.9 * cm, 4.7 * cm, 1.4 * cm, fill=0
        )  # para criar retangulo
        pdf.setFont("Arial", 9)
        pdf.drawString(3.6 * cm, 26.9 * cm, "ORGÃO")
        pdf.setFont("Arial", 10)
        pdf.drawString(
            3.6 * cm, 26 * cm, "SECRETARIA DE ESTADO DE JUSTIÇA E REINTEGRAÇÃO SOCIAL",
        )
        pdf.rect(
            3.5 * cm, 25.9 * cm, 12.4 * cm, 1.4 * cm, fill=0
        )  # para criar retangulo
        pdf.setFont("Arial", 9)
        pdf.drawString(2.1 * cm, 26.9 * cm, "CÓDIGO")
        pdf.rect(2 * cm, 25.9 * cm, 1.5 * cm, 1.4 * cm, fill=0)  # para criar retangulo

        pdf.setFont("Arial-Bold", 10)
        pdf.drawString(2 * cm, 25.5 * cm, "SERVIDOR")
        pdf.setFont("Arial", 9)
        pdf.drawString(2.1 * cm, 25 * cm, "MATRÍCULA")
        pdf.drawString(2.1 * cm, 24.2 * cm, f"{servidor.matricula}")
        pdf.rect(
            2 * cm, 24 * cm, 2.1 * cm, 1.4 * cm, fill=0
        )  # para criar retangulo
        pdf.setFont("Arial", 9)
        pdf.drawString(4.2 * cm, 25 * cm, "VÍNCULO")
        pdf.drawString(4.2 * cm, 24.2 * cm, " ")
        pdf.rect(
            4.1 * cm, 24 * cm, 1.7 * cm, 1.4 * cm, fill=0
        )  # para criar retangulo
        pdf.setFont("Arial", 9)
        pdf.drawString(5.9 * cm, 25 * cm, "NOME")
        pdf.setFont("Arial", 10)
        pdf.drawString(5.9 * cm, 24.2 * cm, f"{servidor.nome} {servidor.sobrenome}")
        pdf.rect(
            5.8 * cm, 24 * cm, 10.1 * cm, 1.4 * cm, fill=0
        )  # para criar retangulo
        pdf.setFont("Arial", 8)
        pdf.drawString(16 * cm, 25 * cm, "CARGA HORÁRIA")
        pdf.drawString(16 * cm, 24.7 * cm, "SEMANAL")
        pdf.setFont("Arial", 10)
        pdf.drawString(16 * cm, 24.2 * cm, f"{servidor.ch}")
        pdf.rect(
            15.9 * cm, 24 * cm, 3 * cm, 1.4 * cm, fill=0
        )  # para criar retangulo
        pdf.setFont("Arial", 8)
        pdf.drawString(18.95 * cm, 25 * cm, "INTERVALO")
        pdf.setFont("Arial", 10)
        pdf.drawString(18.95 * cm, 24.2 * cm, " ")
        pdf.rect(
            18.9 * cm, 24 * cm, 1.7 * cm, 1.4 * cm, fill=0
        )  # para criar retangulo
        pdf.setFont("Arial", 9)
        pdf.drawString(2.3 * cm, 23.2 * cm, "DIA")
        pdf.rect(
            2 * cm, 22.8 * cm, 1.3 * cm, 1.2 * cm, fill=0
        )  # para criar retangulo
        pdf.rect(
            3.3 * cm, 22.8 * cm, 1.2 * cm, 0.6 * cm, fill=0
        )  # para criar retangulo
        pdf.drawString(3.4 * cm, 23 * cm, "HORA")
        pdf.rect(
            4.5 * cm, 22.8 * cm, 2.8 * cm, 0.6 * cm, fill=0
        )  # para criar retangulo
        pdf.drawString(4.7 * cm, 23 * cm, "ASSINATURA")
        pdf.rect(
            3.3 * cm, 23.4 * cm, 4 * cm, 0.6 * cm, fill=0
        )  # para criar retangulo
        pdf.drawString(4.3 * cm, 23.6 * cm, "ENTRADA")

        pdf.rect(
            7.3 * cm, 22.8 * cm, 1.2 * cm, 0.6 * cm, fill=0
        )  # para criar retangulo
        pdf.drawString(7.4 * cm, 23 * cm, "HORA")
        pdf.rect(
            8.5 * cm, 22.8 * cm, 3.1 * cm, 0.6 * cm, fill=0
        )  # para criar retangulo
        pdf.drawString(8.9 * cm, 23 * cm, "ASSINATURA")
        pdf.rect(
            11.6 * cm, 22.8 * cm, 1.2 * cm, 0.6 * cm, fill=0
        )  # para criar retangulo
        pdf.drawString(11.8 * cm, 23 * cm, "HORA")
        pdf.rect(
            12.8 * cm, 22.8 * cm, 3.1 * cm, 0.6 * cm, fill=0
        )  # para criar retangulo
        pdf.drawString(13.3 * cm, 23 * cm, "ASSINATURA")
        pdf.rect(
            7.3 * cm, 23.4 * cm, 8.6 * cm, 0.6 * cm, fill=0
        )  # para criar retangulo
        pdf.drawString(9 * cm, 23.6 * cm, "REFEIÇÃO/DESCANSO")

        pdf.rect(
            15.9 * cm, 23.4 * cm, 4.7 * cm, 0.6 * cm, fill=0
        )  # para criar retangulo
        pdf.drawString(18 * cm, 23.6 * cm, "SAÍDA")
        pdf.rect(
            15.9 * cm, 22.8 * cm, 1.3 * cm, 0.6 * cm, fill=0
        )  # para criar retangulo
        pdf.drawString(16.1 * cm, 23 * cm, "HORA")
        pdf.rect(
            17.2 * cm, 22.8 * cm, 3.4 * cm, 0.6 * cm, fill=0
        )  # para criar retangulo
        pdf.drawString(17.7 * cm, 23 * cm, "ASSINATURA")
        # pdf.rect(3.3 * cm, 23.4 * cm, 4.3 * cm, 0.6 * cm, fill=0)  # para criar retangulo
                # c.drawString(4.3 * cm, 23.6 * cm, "ENTRADA")

            ##Para geração das linhas e datas do dia do mes
        total = range(1, 31 + 1, 1)
        x_alt = 22.2 + 0.6
        x_alt_data = 22.4 + 0.6
        for x in total:
            x_alt = x_alt - 0.6
            x_alt_data = x_alt_data - 0.6
            pdf.setFont("Arial", 10)  # DIA
            pdf.drawString(2.4 * cm, x_alt_data * cm, f"{x}")
            pdf.rect(
                2 * cm, x_alt * cm, 1.3 * cm, 0.6 * cm, fill=0
            )  # para criar retangulo
            pdf.rect(
                3.3 * cm, x_alt * cm, 1.2 * cm, 0.6 * cm, fill=0
            )  # para criar retangulo
            pdf.rect(
                4.5 * cm, x_alt * cm, 2.8 * cm, 0.6 * cm, fill=0
            )  # para criar retangulo
            pdf.rect(
                7.3 * cm, x_alt * cm, 1.2 * cm, 0.6 * cm, fill=0
            )  # para criar retangulo
            pdf.rect(
                8.5 * cm, x_alt * cm, 3.1 * cm, 0.6 * cm, fill=0
            )  # para criar retangulo
            pdf.rect(
                11.6 * cm, x_alt * cm, 1.2 * cm, 0.6 * cm, fill=0
            )  # para criar retangulo
            pdf.rect(
                12.8 * cm, x_alt * cm, 3.1 * cm, 0.6 * cm, fill=0
            )  # para criar retangulo
            pdf.rect(15.9 * cm, x_alt * cm, 1.3 * cm, 0.6 * cm, fill=0)
            pdf.rect(
                17.2 * cm, x_alt * cm, 3.4 * cm, 0.6 * cm, fill=0
            )  # para criar retangulo

        pdf.rect(
            2 * cm, 0.6 * cm, 2.5 * cm, 3.5 * cm, fill=0
        )  # para criar retangulo
        pdf.setFont("Arial", 7.5)  # DIA
        pdf.drawCentredString(3.25 * cm, 3.65 * cm, "EM CASO DE")
        pdf.drawCentredString(3.25 * cm, 3.35 * cm, "ABONO A CHEFIA")
        pdf.drawCentredString(3.25 * cm, 3.05 * cm, "IMEDIATA DEVERÁ")
        pdf.drawCentredString(3.25 * cm, 2.75 * cm, "ESPECIFICAR O")
        pdf.drawCentredString(3.25 * cm, 2.45 * cm, "DIA A SER")
        pdf.drawCentredString(3.25 * cm, 2.15 * cm, "ABONADO,")
        pdf.drawCentredString(3.25 * cm, 1.85 * cm, "DESCREVER O")
        pdf.drawCentredString(3.25 * cm, 1.55 * cm, "MOTIVO E")
        pdf.drawCentredString(3.25 * cm, 1.25 * cm, "ASSINAR.")

        pdf.setFont("Arial", 8)  # DIA
        pdf.drawCentredString(5.2 * cm, 3.65 * cm, "DIA")
        pdf.drawCentredString(7.7 * cm, 3.65 * cm, "MOTIVO")
        pdf.drawCentredString(11.5 * cm, 3.65 * cm, "ASSINATURA")
        x_jus = 4.1
        for x in range(0, 7, 1):
            x_jus = x_jus - 0.5
            pdf.rect(
                4.5 * cm, x_jus * cm, 1.3 * cm, 0.5 * cm, fill=0
            )  # para criar retangulo
            pdf.rect(
                5.8 * cm, x_jus * cm, 4.2 * cm, 0.5 * cm, fill=0
            )  # para criar retangulo
            pdf.rect(
                10 * cm, x_jus * cm, 3 * cm, 0.5 * cm, fill=0
            )  # para criar retangulo

        pdf.setFont("Arial-Bold", 8)  # DIA
        pdf.drawString(13.3 * cm, 3.7 * cm, "SERVIDOR")
        pdf.setFont("Arial", 7)  # DIA
        pdf.drawString(
            13.3 * cm,
            3.5 * cm,
            "Reconheço como verdadeiras as anotações sobre a minha",
        )
        pdf.drawString(
            13.3 * cm,
            3.2 * cm,
            "assiduidade e pontualidade e as assumo na integra.",
        )
        pdf.rect(
            13.1 * cm, 3.1 * cm, 7.5 * cm, 1 * cm, fill=0
        )  # para criar retangulo
        pdf.setFont("Arial", 7)  # DIA
        pdf.drawString(13.3 * cm, 2.8 * cm, "DATA")
        pdf.drawString(16.3 * cm, 2.8 * cm, "ASSINATURA")
        pdf.rect(
            13.1 * cm, 2.1 * cm, 3 * cm, 1 * cm, fill=0
        )  # para criar retangulo
                # ADD DATA
        pdf.rect(
            16.1 * cm, 2.1 * cm, 4.5 * cm, 1 * cm, fill=0
        )  # para criar retangulo

        pdf.setFont("Arial-Bold", 8)  # DIA
        pdf.drawString(13.1 * cm, 1.7 * cm, "CHEFIA IMEDIATA")
        pdf.setFont("Arial", 7)  # DIA
        pdf.drawString(13.3 * cm, 1.3 * cm, "DATA")
        pdf.drawString(16.3 * cm, 1.3 * cm, "ASSINATURA")
        pdf.rect(
            13.1 * cm, 0.6 * cm, 3 * cm, 1 * cm, fill=0
        )  # para criar retangulo
        pdf.rect(
            16.1 * cm, 0.6 * cm, 4.5 * cm, 1 * cm, fill=0
        )  # para criar retangulo
        pdf.showPage()

    pdf.save()

    return response

@checked_debug_decorador
def folha_ponto_servidor(request, servidor_id, mes, ano):
    """View para exibir a folha de ponto de um servidor específico"""
    
    servidor = get_object_or_404(Servidores, id=servidor_id)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="folha_ponto_{servidor.nome_exibir}_{mes}.pdf"'
    
    pdf = canvas.Canvas(response, pagesize=A4)
    pdf.setAuthor('OgliTech')
    pdf.setLineWidth(0.5) # Espessura da linha
    pdf.setStrokeColorRGB(0, 0, 0, 0.7) #Cor da linha
    largura, altura = A4

    pdf.drawImage(
        os.path.join(settings.BASE_DIR, 'staticfiles', 'servidores','img', 'logo.png'),
        0.4 * cm,
        27.8 * cm,
        width=1.5 * cm,
        height=1.5 * cm,
    )
    pdf.setFont("Arial-Bold", 10)
    pdf.drawString(2 * cm, 28.9 * cm, "ESTADO DE SANTA CATARINA")
    pdf.drawString(16.5 * cm, 29 * cm, "CONTROLE DE PONTO")
    pdf.setFont("Arial", 8)
    pdf.drawString(16 * cm, 28.3 * cm, "MÊS/ANO")
    pdf.setFont("Arial", 9)
    pdf.drawString(
        16 * cm, 27.6 * cm, f"{mes}/{ano}"
    )
    pdf.rect(
        15.9 * cm, 27.3 * cm, 4.7 * cm, 1.4 * cm, fill=0
    )
    pdf.setFont("Arial", 8)
    pdf.drawString(16 * cm, 26.9 * cm, "LOTAÇÃO (SIGLA)")
    pdf.setFont("Arial", 10)
    pdf.drawString(
        16.3 * cm, 26 * cm, "UPA20"
    )
    pdf.rect(
        15.9 * cm, 25.9 * cm, 4.7 * cm, 1.4 * cm, fill=0
    )  # para criar retangulo
    pdf.setFont("Arial", 9)
    pdf.drawString(3.6 * cm, 26.9 * cm, "ORGÃO")
    pdf.setFont("Arial", 10)
    pdf.drawString(
        3.6 * cm, 26 * cm, "SECRETARIA DE ESTADO DE JUSTIÇA E REINTEGRAÇÃO SOCIAL",
    )
    pdf.rect(
        3.5 * cm, 25.9 * cm, 12.4 * cm, 1.4 * cm, fill=0
    )  # para criar retangulo
    pdf.setFont("Arial", 9)
    pdf.drawString(2.1 * cm, 26.9 * cm, "CÓDIGO")
    pdf.rect(2 * cm, 25.9 * cm, 1.5 * cm, 1.4 * cm, fill=0)  # para criar retangulo

    pdf.setFont("Arial-Bold", 10)
    pdf.drawString(2 * cm, 25.5 * cm, "SERVIDOR")
    pdf.setFont("Arial", 9)
    pdf.drawString(2.1 * cm, 25 * cm, "MATRÍCULA")
    pdf.drawString(2.1 * cm, 24.2 * cm, f"{servidor.matricula}")
    pdf.rect(
        2 * cm, 24 * cm, 2.1 * cm, 1.4 * cm, fill=0
    )  # para criar retangulo
    pdf.setFont("Arial", 9)
    pdf.drawString(4.2 * cm, 25 * cm, "VÍNCULO")
    pdf.drawString(4.2 * cm, 24.2 * cm, " ")
    pdf.rect(
        4.1 * cm, 24 * cm, 1.7 * cm, 1.4 * cm, fill=0
    )  # para criar retangulo
    pdf.setFont("Arial", 9)
    pdf.drawString(5.9 * cm, 25 * cm, "NOME")
    pdf.setFont("Arial", 10)
    pdf.drawString(5.9 * cm, 24.2 * cm, f"{servidor.nome} {servidor.sobrenome}")
    pdf.rect(
        5.8 * cm, 24 * cm, 10.1 * cm, 1.4 * cm, fill=0
    )  # para criar retangulo
    pdf.setFont("Arial", 8)
    pdf.drawString(16 * cm, 25 * cm, "CARGA HORÁRIA")
    pdf.drawString(16 * cm, 24.7 * cm, "SEMANAL")
    pdf.setFont("Arial", 10)
    pdf.drawString(16 * cm, 24.2 * cm, f"{servidor.ch}")
    pdf.rect(
        15.9 * cm, 24 * cm, 3 * cm, 1.4 * cm, fill=0
    )  # para criar retangulo
    pdf.setFont("Arial", 8)
    pdf.drawString(18.95 * cm, 25 * cm, "INTERVALO")
    pdf.setFont("Arial", 10)
    pdf.drawString(18.95 * cm, 24.2 * cm, " ")
    pdf.rect(
        18.9 * cm, 24 * cm, 1.7 * cm, 1.4 * cm, fill=0
    )  # para criar retangulo
    pdf.setFont("Arial", 9)
    pdf.drawString(2.3 * cm, 23.2 * cm, "DIA")
    pdf.rect(
        2 * cm, 22.8 * cm, 1.3 * cm, 1.2 * cm, fill=0
    )  # para criar retangulo
    pdf.rect(
        3.3 * cm, 22.8 * cm, 1.2 * cm, 0.6 * cm, fill=0
    )  # para criar retangulo
    pdf.drawString(3.4 * cm, 23 * cm, "HORA")
    pdf.rect(
        4.5 * cm, 22.8 * cm, 2.8 * cm, 0.6 * cm, fill=0
    )  # para criar retangulo
    pdf.drawString(4.7 * cm, 23 * cm, "ASSINATURA")
    pdf.rect(
        3.3 * cm, 23.4 * cm, 4 * cm, 0.6 * cm, fill=0
    )  # para criar retangulo
    pdf.drawString(4.3 * cm, 23.6 * cm, "ENTRADA")

    pdf.rect(
        7.3 * cm, 22.8 * cm, 1.2 * cm, 0.6 * cm, fill=0
    )  # para criar retangulo
    pdf.drawString(7.4 * cm, 23 * cm, "HORA")
    pdf.rect(
        8.5 * cm, 22.8 * cm, 3.1 * cm, 0.6 * cm, fill=0
    )  # para criar retangulo
    pdf.drawString(8.9 * cm, 23 * cm, "ASSINATURA")
    pdf.rect(
        11.6 * cm, 22.8 * cm, 1.2 * cm, 0.6 * cm, fill=0
    )  # para criar retangulo
    pdf.drawString(11.8 * cm, 23 * cm, "HORA")
    pdf.rect(
        12.8 * cm, 22.8 * cm, 3.1 * cm, 0.6 * cm, fill=0
    )  # para criar retangulo
    pdf.drawString(13.3 * cm, 23 * cm, "ASSINATURA")
    pdf.rect(
        7.3 * cm, 23.4 * cm, 8.6 * cm, 0.6 * cm, fill=0
    )  # para criar retangulo
    pdf.drawString(9 * cm, 23.6 * cm, "REFEIÇÃO/DESCANSO")

    pdf.rect(
        15.9 * cm, 23.4 * cm, 4.7 * cm, 0.6 * cm, fill=0
    )  # para criar retangulo
    pdf.drawString(18 * cm, 23.6 * cm, "SAÍDA")
    pdf.rect(
        15.9 * cm, 22.8 * cm, 1.3 * cm, 0.6 * cm, fill=0
    )  # para criar retangulo
    pdf.drawString(16.1 * cm, 23 * cm, "HORA")
    pdf.rect(
        17.2 * cm, 22.8 * cm, 3.4 * cm, 0.6 * cm, fill=0
    )  # para criar retangulo
    pdf.drawString(17.7 * cm, 23 * cm, "ASSINATURA")
    # pdf.rect(3.3 * cm, 23.4 * cm, 4.3 * cm, 0.6 * cm, fill=0)  # para criar retangulo
            # c.drawString(4.3 * cm, 23.6 * cm, "ENTRADA")

        ##Para geração das linhas e datas do dia do mes
    total = range(1, 31 + 1, 1)
    x_alt = 22.2 + 0.6
    x_alt_data = 22.4 + 0.6
    for x in total:
        x_alt = x_alt - 0.6
        x_alt_data = x_alt_data - 0.6
        pdf.setFont("Arial", 10)  # DIA
        pdf.drawString(2.4 * cm, x_alt_data * cm, f"{x}")
        pdf.rect(
            2 * cm, x_alt * cm, 1.3 * cm, 0.6 * cm, fill=0
        )  # para criar retangulo
        pdf.rect(
            3.3 * cm, x_alt * cm, 1.2 * cm, 0.6 * cm, fill=0
        )  # para criar retangulo
        pdf.rect(
            4.5 * cm, x_alt * cm, 2.8 * cm, 0.6 * cm, fill=0
        )  # para criar retangulo
        pdf.rect(
            7.3 * cm, x_alt * cm, 1.2 * cm, 0.6 * cm, fill=0
        )  # para criar retangulo
        pdf.rect(
            8.5 * cm, x_alt * cm, 3.1 * cm, 0.6 * cm, fill=0
        )  # para criar retangulo
        pdf.rect(
            11.6 * cm, x_alt * cm, 1.2 * cm, 0.6 * cm, fill=0
        )  # para criar retangulo
        pdf.rect(
            12.8 * cm, x_alt * cm, 3.1 * cm, 0.6 * cm, fill=0
        )  # para criar retangulo
        pdf.rect(15.9 * cm, x_alt * cm, 1.3 * cm, 0.6 * cm, fill=0)
        pdf.rect(
            17.2 * cm, x_alt * cm, 3.4 * cm, 0.6 * cm, fill=0
        )  # para criar retangulo

    pdf.rect(
        2 * cm, 0.6 * cm, 2.5 * cm, 3.5 * cm, fill=0
    )  # para criar retangulo
    pdf.setFont("Arial", 7.5)  # DIA
    pdf.drawCentredString(3.25 * cm, 3.65 * cm, "EM CASO DE")
    pdf.drawCentredString(3.25 * cm, 3.35 * cm, "ABONO A CHEFIA")
    pdf.drawCentredString(3.25 * cm, 3.05 * cm, "IMEDIATA DEVERÁ")
    pdf.drawCentredString(3.25 * cm, 2.75 * cm, "ESPECIFICAR O")
    pdf.drawCentredString(3.25 * cm, 2.45 * cm, "DIA A SER")
    pdf.drawCentredString(3.25 * cm, 2.15 * cm, "ABONADO,")
    pdf.drawCentredString(3.25 * cm, 1.85 * cm, "DESCREVER O")
    pdf.drawCentredString(3.25 * cm, 1.55 * cm, "MOTIVO E")
    pdf.drawCentredString(3.25 * cm, 1.25 * cm, "ASSINAR.")

    pdf.setFont("Arial", 8)  # DIA
    pdf.drawCentredString(5.2 * cm, 3.65 * cm, "DIA")
    pdf.drawCentredString(7.7 * cm, 3.65 * cm, "MOTIVO")
    pdf.drawCentredString(11.5 * cm, 3.65 * cm, "ASSINATURA")
    x_jus = 4.1
    for x in range(0, 7, 1):
        x_jus = x_jus - 0.5
        pdf.rect(
            4.5 * cm, x_jus * cm, 1.3 * cm, 0.5 * cm, fill=0
        )  # para criar retangulo
        pdf.rect(
            5.8 * cm, x_jus * cm, 4.2 * cm, 0.5 * cm, fill=0
        )  # para criar retangulo
        pdf.rect(
            10 * cm, x_jus * cm, 3 * cm, 0.5 * cm, fill=0
        )  # para criar retangulo

    pdf.setFont("Arial-Bold", 8)  # DIA
    pdf.drawString(13.3 * cm, 3.7 * cm, "SERVIDOR")
    pdf.setFont("Arial", 7)  # DIA
    pdf.drawString(
        13.3 * cm,
        3.5 * cm,
        "Reconheço como verdadeiras as anotações sobre a minha",
    )
    pdf.drawString(
        13.3 * cm,
        3.2 * cm,
        "assiduidade e pontualidade e as assumo na integra.",
    )
    pdf.rect(
        13.1 * cm, 3.1 * cm, 7.5 * cm, 1 * cm, fill=0
    )  # para criar retangulo
    pdf.setFont("Arial", 7)  # DIA
    pdf.drawString(13.3 * cm, 2.8 * cm, "DATA")
    pdf.drawString(16.3 * cm, 2.8 * cm, "ASSINATURA")
    pdf.rect(
        13.1 * cm, 2.1 * cm, 3 * cm, 1 * cm, fill=0
    )  # para criar retangulo
            # ADD DATA
    pdf.rect(
        16.1 * cm, 2.1 * cm, 4.5 * cm, 1 * cm, fill=0
    )  # para criar retangulo

    pdf.setFont("Arial-Bold", 8)  # DIA
    pdf.drawString(13.1 * cm, 1.7 * cm, "CHEFIA IMEDIATA")
    pdf.setFont("Arial", 7)  # DIA
    pdf.drawString(13.3 * cm, 1.3 * cm, "DATA")
    pdf.drawString(16.3 * cm, 1.3 * cm, "ASSINATURA")
    pdf.rect(
        13.1 * cm, 0.6 * cm, 3 * cm, 1 * cm, fill=0
    )  # para criar retangulo
    pdf.rect(
        16.1 * cm, 0.6 * cm, 4.5 * cm, 1 * cm, fill=0
    )  # para criar retangulo
    pdf.showPage()

    pdf.save()

    return response

def frase_motivacional(request):
    """Proxy para a ZenQuotes API com tradução via MyMemory."""
    KEYWORDS = {
        'love': 'Amor',
        'confidence': 'Confiança',
        'courage': 'Coragem',
        'dreams': 'Sonhos',
        'freedom': 'Liberdade',
        'future': 'Futuro',
        'happiness': 'Felicidade',
        'inspiration': 'Inspiração',
        'life': 'Vida',
        'success': 'Sucesso',
        'time': 'Tempo',
    }

    FALLBACKS = [
        {'q': 'O segredo de avançar é começar.', 'a': 'Mark Twain', 'keyword_pt': 'Sucesso'},
        {'q': 'No meio de toda dificuldade existe uma oportunidade.', 'a': 'Albert Einstein', 'keyword_pt': 'Coragem'},
        {'q': 'A vida é o que acontece enquanto você está ocupado fazendo outros planos.', 'a': 'John Lennon', 'keyword_pt': 'Vida'},
        {'q': 'Espalhe amor por onde você for.', 'a': 'Madre Teresa', 'keyword_pt': 'Amor'},
        {'q': 'O futuro pertence àqueles que acreditam na beleza dos seus sonhos.', 'a': 'Eleanor Roosevelt', 'keyword_pt': 'Sonhos'},
    ]

    keyword_en = random.choice(list(KEYWORDS.keys()))
    keyword_pt = KEYWORDS[keyword_en]

    def traduzir(texto):
        """Traduz inglês → português via MyMemory (gratuita, sem chave)."""
        try:
            url = f"https://api.mymemory.translated.net/get?q={texto}&langpair=en|pt-BR"
            resp = http_requests.get(url, timeout=4)
            resp.raise_for_status()
            data = resp.json()
            traducao = data.get('responseData', {}).get('translatedText', '')
            if traducao and data.get('responseStatus') == 200:
                return traducao
        except Exception:
            pass
        return texto  # Retorna original se falhar

    try:
        response = http_requests.get(
            'https://zenquotes.io/api/random',
            timeout=5,
            headers={'User-Agent': 'PIEVDCS/1.0'},
        )
        response.raise_for_status()
        data = response.json()
        quote = data[0]
        frase_traduzida = traduzir(quote['q'])
        return JsonResponse({
            'q': frase_traduzida,
            'a': quote['a'],
            'keyword_pt': keyword_pt,
        })
    except Exception:
        fallback = random.choice(FALLBACKS)
        return JsonResponse(fallback)


def extrair_dados_primeira_pagina(arquivo_pdf):
    arquivo_pdf.seek(0)
    with pdfplumber.open(arquivo_pdf) as pdf:
        texto = (pdf.pages[0].extract_text() or "").strip()
        texto = texto.replace("\n", " ")
        texto = re.sub(r"\s+", " ", texto).strip()

    #print(f"Texto extraído da primeira página:\n\n\n", texto)  # Debug: exibe o texto extraído
    dados = {
        "nome": "",
        "matricula": "",
        "processo": "",
        "qtd_obras": "",
    }

    m_nome = re.search(r"aluno\s*:?\s*(.+?)(?=,\sregularmente|\s,)", texto,re.IGNORECASE | re.DOTALL,)
    m_mat =  re.search(r"n[uú]mero\s+de\s+inscri[cç][aã]o\s*([0-9.-]+)", texto,re.IGNORECASE,)
    m_proc = re.search(r"Processo:\s*([\w./-]+)", texto, re.IGNORECASE)
    m_qtd_obras = re.search(r"leitura\s+de\s+(\d+)\s+obra(s)", texto,re.IGNORECASE,)

    if m_nome:
        dados["nome"] = " ".join(m_nome.group(1).split()).strip()
    if m_mat: 
        dados["matricula"] = m_mat.group(1).strip()
    if m_proc: 
        dados["processo"] = m_proc.group(1).strip()
    if m_qtd_obras:
        dados["qtd_obras"] = m_qtd_obras.group(1).strip()
    return dados

def _desenhar_cabecalho_rodape(c):
    logo_path = os.path.join(
        settings.BASE_DIR, 'servidores', 'static', 'servidores', 'img', 'logopp.png'
    )

    # --- Cabeçalho ---
    c.drawImage(logo_path, 40, 792, width=52, height=52, preserveAspectRatio=True, mask='auto')

    c.setFont("Arial-Bold", 9)
    c.drawString(100, 833, "ESTADO DE SANTA CATARINA")
    c.setFont("Arial", 8)
    c.drawString(100, 820, "SECRETARIA DE ESTADO DE JUSTIÇA E REINTEGRAÇÃO SOCIAL")
    c.drawString(100, 808, "PRESÍDIO REGIONAL DE MARAVILHA")
    c.setFont("Arial-Bold", 8)
    c.drawString(100, 796, "POLÍCIA PENAL")

    c.setLineWidth(0.8)
    c.line(40, 785, 555, 785)

    # --- Rodapé ---
    c.line(40, 72, 555, 72)
    c.setFont("Arial-Bold", 11)
    c.drawCentredString(298, 60, "POLÍCIA PENAL DE SANTA CATARINA")
    c.setFont("Arial", 11)
    c.drawCentredString(298, 46, "Presídio Regional de Maravilha")
    c.drawCentredString(298, 32, "Avenida Sul Brasil, 1607, Madalozzo, CEP 89874-000, Maravilha/SC")
    c.drawCentredString(298, 18, "Telefone: (49) 3664 6672 / e-mail: pr29@pp.sc.gov.br")

def gerar_pdf_oficio_trabalho(dados, numero_oficio, nome_servidor, nome_juiz, nome_comarca):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    _desenhar_cabecalho_rodape(c) # Função para desenhar o cabeçalho e rodapé
    c.setFont("Arial-Bold", 14)
    c.drawString(72, 750, "OFÍCIO DE ENCAMINHAMENTO - SETOR DE TRABALHO")
    c.setFont("Arial", 10)
    c.drawString(72, 720, f"Ofício nº {numero_oficio}")
    c.drawString(72, 700, f"Servidor selecionado: {nome_servidor}")
    c.drawString(72, 680, f"Nome extraído: {dados.get('nome', '-')}")
    c.drawString(72, 660, f"Matrícula: {dados.get('matricula', '-')}")
    c.drawString(72, 640, f"Processo: {dados.get('processo', '-')}")
    c.drawString(72, 620, f"Magistrado(a): {nome_juiz}")
    c.drawString(72, 600, f"Comarca/Juízo: {nome_comarca}")
    c.save()
    buffer.seek(0)
    return buffer

def gerar_pdf_oficio_estudo(dados, numero_oficio, nome_servidor, nome_juiz, nome_comarca):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    _desenhar_cabecalho_rodape(c) # Função para desenhar o cabeçalho e rodapé
    c.setFont("Arial-Bold", 14)
    c.drawString(72, 750, "OFÍCIO DE ENCAMINHAMENTO - SETOR DE ESTUDO")
    c.setFont("Arial", 10)
    c.drawString(72, 720, f"Ofício nº {numero_oficio}")
    c.drawString(72, 700, f"Aluno(a): {dados.get('nome', '-')}")
    c.drawString(72, 680, f"Matrícula: {dados.get('matricula', '-')}")
    c.drawString(72, 660, f"Referência: {dados.get('processo', '-')}")
    c.drawString(72, 640, f"Magistrado(a): {nome_juiz}")
    c.drawString(72, 620, f"Comarca/Juízo: {nome_comarca}")
    c.drawString(72, 600, "Encaminhamos para deliberação.")
    c.save()
    buffer.seek(0)
    return buffer

def gerar_pdf_oficio_resenha(dados, numero_oficio, nome_servidor, nome_juiz, nome_comarca):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    _desenhar_cabecalho_rodape(c) # Função para desenhar o cabeçalho e rodapé
    c.setFont("Arial-Bold", 14)
    c.drawString(72, 750, "OFÍCIO DE ENCAMINHAMENTO - RESENHA DE LIVROS")
    c.setFont("Arial", 10)
    c.drawString(72, 720, f"Ofício nº {numero_oficio}")
    c.drawString(72, 700, f"Interno(a): {dados.get('nome', '-')}")
    c.drawString(72, 680, f"ID: {dados.get('matricula', '-')}")
    c.drawString(72, 660, f"Quantidade de resenhas: {dados.get('qtd_obras', '-')}")
    c.drawString(72, 630, "Resenha anexada para análise.")
    c.drawString(72, 610, f"Magistrado(a): {nome_juiz}")
    c.drawString(72, 590, f"Comarca/Juízo: {nome_comarca}")
    c.save()
    buffer.seek(0)
    return buffer

TIPO_OFICIO_ARQUIVO = {
    "oficio_1": "trabalho",
    "oficio_2": "estudo",
    "oficio_3": "resenha",
}

def extrair_texto_pdf_gera_oficio(files, numero_oficio, tipo_oficio, nome_servidor, nome_juiz, nome_comarca):
    geradores = {
        "oficio_1": gerar_pdf_oficio_trabalho,
        "oficio_2": gerar_pdf_oficio_estudo,
        "oficio_3": gerar_pdf_oficio_resenha,
    }
    gerador = geradores.get(tipo_oficio, gerar_pdf_oficio_trabalho)
    tipo_slug = TIPO_OFICIO_ARQUIVO.get(tipo_oficio, "trabalho")

    try:
        numero_inicial = int(numero_oficio)
    except (TypeError, ValueError):
        numero_inicial = 0

    documentos = []

    for indice, arquivo in enumerate(files):
        numero_atual = str(numero_inicial + indice)
        dados = extrair_dados_primeira_pagina(arquivo)

        writer = PdfWriter()

        oficio_pdf = gerador(dados, numero_atual, nome_servidor, nome_juiz, nome_comarca)
        oficio_reader = PdfReader(oficio_pdf)
        for pagina in oficio_reader.pages:
            writer.add_page(pagina)

        arquivo.seek(0)
        original_reader = PdfReader(arquivo)
        for pagina in original_reader.pages:
            writer.add_page(pagina)

        saida = BytesIO()
        writer.write(saida)
        saida.seek(0)

        nome_base = os.path.splitext(arquivo.name)[0]
        nome_doc = f"oficio_{tipo_slug}_{numero_atual}_{nome_base}.pdf"
        documentos.append((nome_doc, saida.getvalue()))

    return documentos



@checked_debug_decorador
def gerador_oficios(request):
    """Exibe o formulário de geração de ofícios e processa o envio."""

    usuarios = (
        Servidores.objects
        .filter(status_ativo=True, setor="ADMINISTRATIVO")
        .order_by("nome_exibir")
        .only("id", "nome_exibir", "matricula")
    )

    unidade = UnidadeOficio.objects.filter(sigla="PR29").first()

    contexto_base = {
        "ano_corrente": timezone.now().year,
        "usuarios": usuarios,
        "nome_juiz": unidade.nome_magistrado if unidade else "Juiz Não Cadastrado",
        "nome_comarca": unidade.nome_juizo if unidade else "Comarca Não Cadastrada",
    }

    if request.method == "POST":
        numero_oficio = request.POST.get("numero_oficio", "").strip()
        tipo_oficio = request.POST.get("tipo_oficio", "").strip()
        servidor_id = request.POST.get("usuario_id", "").strip()
        arquivos_pdf = request.FILES.getlist("arquivos_pdf")
        nomes_arquivos = [arquivo.name for arquivo in arquivos_pdf]

        if not arquivos_pdf:
            contexto = {
                **contexto_base,
                "numero_oficio": numero_oficio,
                "tipo_oficio": tipo_oficio,
                "servidor_id": servidor_id,
                "nomes_arquivos": nomes_arquivos,
                "erro": "Selecione ao menos um PDF.",
            }
            return render(request, "gerador_oficios.html", contexto)

        servidor_obj = usuarios.filter(id=servidor_id).first()
        nome_servidor = servidor_obj.nome_exibir if servidor_obj else "Servidor não informado"

        pdf_final = extrair_texto_pdf_gera_oficio(
            arquivos_pdf,
            numero_oficio,
            tipo_oficio,
            nome_servidor,
            nome_juiz=contexto_base["nome_juiz"],
            nome_comarca=contexto_base["nome_comarca"],
        )

        tipo_slug = TIPO_OFICIO_ARQUIVO.get(tipo_oficio, "trabalho")

        # Se só tiver 1 documento final, baixa PDF direto
        if len(pdf_final) == 1:
            nome_arquivo, conteudo_pdf = pdf_final[0]
            response = HttpResponse(conteudo_pdf, content_type="application/pdf")
            response["Content-Disposition"] = f'attachment; filename="{nome_arquivo}"'
            return response

        # Se tiver mais de 1, baixa ZIP
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
            for nome_arquivo, conteudo_pdf in pdf_final:
                zip_file.writestr(nome_arquivo, conteudo_pdf)

        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer.getvalue(), content_type="application/zip")
        response["Content-Disposition"] = f'attachment; filename="oficios_{tipo_slug}.zip"'
        return response

    return render(request, "gerador_oficios.html", contexto_base)