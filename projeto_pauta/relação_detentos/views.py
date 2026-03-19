import pdfplumber

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm  # Ensure cm is imported
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

import pandas as pd
import json
import datetime
import locale
import io 
import os
import math
from concurrent.futures import ProcessPoolExecutor, as_completed

from django.urls import reverse
from django.http import HttpResponseRedirect
from django.templatetags.static import static
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.http import JsonResponse, FileResponse, HttpResponse
from django.core.files.storage import FileSystemStorage
from .forms.geradores import DescricaoKitHigieneForm, TermoRoupariaForm 

from django.db.models import Case, When, Value, Max, Count, Q
from django.db.models.functions import Concat
from django.utils import timezone

from .process_table import process_pdf, process_regime_pdf, exctrai_date_exit
from .models import Relacao, DescricaoKitHigiene, Descricao_termo_rouparia, CalculoAlimentacao


from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.generic import NameObject, createStringObject

locale.setlocale(locale.LC_ALL, 'pt_BR.utf8')


# Registre Arial e Arial-Bold (se quiser usar negrito)
# Registre Arial e Arial-Bold (se quiser usar negrito)
# Caminhos relativos à pasta base do projeto
arial_path = os.path.join(settings.BASE_DIR, 'projeto_pauta', 'static', 'fonts', 'arial.ttf')
arial_bold_path = os.path.join(settings.BASE_DIR, 'projeto_pauta', 'static', 'fonts', 'arialbd.ttf')

# Registra as fontes
pdfmetrics.registerFont(TTFont('Arial', arial_path))
pdfmetrics.registerFont(TTFont('Arial-Bold', arial_bold_path))

ANO_CORRENTE = timezone.now().year

if settings.DEBUG:
    from projeto_pauta.decoradores.calcula_tempo import calcula_tempo, calcula_tempo_fun
    checked_debug_decorador = calcula_tempo
    check_login_required = lambda x: x
    print_debug = True
else:
    print_debug = False
    checked_debug_decorador = lambda x: x
    check_login_required = login_required

@checked_debug_decorador
@check_login_required
def relacao_list(request):
    '''
    Exibe uma lista com os detentos e suas informações
    Returns:
        render com a pagina renderizada e com variaveis das informações
    
    Args:
        Request: Requisição da  página    
    
    Template:
        pauta/template/relacao_list.html
    '''

    # Ordem para local_alocacao (A, B, D)
    local_alocacao_order = Case(
        When(local_alocacao='A', then=Value(1)),
        When(local_alocacao='B', then=Value(2)),
        When(local_alocacao='C', then=Value(3)),
        When(local_alocacao='D', then=Value(4)),
        When(local_alocacao='E', then=Value(5)),
    )
    


    regime_order = Case(
        When(regime='PRO', then=Value(1)),
        When(regime='PRE', then=Value(2)),
        When(regime='F', then=Value(3)),
        When(regime='SA', then=Value(4)),
    )

    relacoes = Relacao.objects.all().annotate(
        local_alocacao_order=local_alocacao_order,
        regime_order=regime_order
    ).order_by('local_alocacao_order', 'local_residencia', 'nome')

    regime_map = {
        'PRO': 'Temporária',
        'F': 'Fechado',
        'SA': 'Semiaberto',
        'TOR': 'Tornozeleira',
        'PRE': 'Preventiva',
        'A' : 'Alimentos'
    }
    #cria a variavel para passar a aquantidade de presos no fechado
    qtd_fechado = relacoes.filter(local_alocacao='F').count()
    qtd_semiaberto = relacoes.filter(local_alocacao='SA').count()
    #qtd_preventiva = relacoes.filter(regime='PRE').count
    qtd_preventiva = 0 # Atualmente não utilizado
    qtd_total = qtd_fechado + qtd_semiaberto + qtd_preventiva
    #print(qtd_fechado)

    local_alocacao_map = {
        'F' : 'Fechado',
        'SA' : 'Semiaberto',
        'TOR' : 'Liberado'
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
        'qtd_preventiva' : qtd_preventiva, #quantidade de preventivos
    })

@csrf_exempt
def salvar_alteracoes(request):
    """
    Responsavél por salvar as informações alteradas na lista de detentos
    Args:
        request (HttpRequest): Requisição HTTP contendo os dados em JSON no corpo da requisição.

    Returns:
        JsonResponse: Resposta JSON indicando sucesso ou falha da operação.
    """
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
                detento.observacoes = item.get('observacao')
                
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


def upload_pdf(request):
    '''
    Recebe o arquivo PDF enviado pelo usuário, processa o conteúdo para extrair informações relevantes e atualiza o banco de dados com esses dados.

    Returns:
        render com a pagina renderizada e atualizada com 1 de 3 atualizaçoes
    
    Args:
        Arquivo PDF, oriundo do sistema IPEN relatorio 1.9    
    
    Template:
        pauta/template/relacao_list.html
    '''
    if request.method == 'POST' and request.FILES.get('pdfFile'):
        pdf_file = request.FILES['pdfFile']
        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'relatorio1-9'))
        filename = fs.save(pdf_file.name, pdf_file)
        file_path = fs.path(filename)

        process_pdf(file_path)

        return redirect('relação_detentos:view_termo_rouparia')
    return render(request, 'relacao_list.html')

def upload_regime_pdf(request):
    if request.method == 'POST' and request.FILES.get('regimePdfFile'):
        pdf_file = request.FILES['regimePdfFile']
        fs = FileSystemStorage()
        filename = fs.save(pdf_file.name, pdf_file)
        file_path = fs.path(filename)
        #print(f'Nome do arquivo: {filename} \n Caminho do arquivo: {file_path}')

        updated_records = process_regime_pdf(file_path)
        

        if updated_records:
            message = f'Regimes atualizados: {len(updated_records)}'
        else:
            message = 'Nenhum regime foi atualizado.'

        return redirect(f'/relacoes/?message={message}')
    return render(request, 'relacao_list.html')


def exctrai_date_exit_view(request):
    if request.method == 'POST' and request.FILES.get('progressaoPdfFile'):
        pdf_file = request.FILES['progressaoPdfFile']
        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'relatorio_progressao'))
        filename = fs.save(pdf_file.name, pdf_file)
        file_path = fs.path(filename)
        # print(f'Nome do arquivo: {filename} \n Caminho do arquivo: {file_path}')

        updated_records = exctrai_date_exit(file_path)

        if updated_records:
            message = f'Regimes atualizados: {len(updated_records)}'
        else:
            message = 'Nenhum regime foi atualizado.'

        return redirect(f'/relacoes/?message={message}')
    return render(request, 'relacao_list.html')


@checked_debug_decorador
def view_termo_rouparia(request):
    '''
    Busca e configura as informações para gerar o termo de rouparia
    Returns:
        Pagina renderizada e com variaveis das configurações do termo de rouparia
    
    Args:
        Request: Requisição da  página    
    
    Template:
        relação_detentos/template/gerador_rouparia.html
    '''
    detento = None
    numero_rouparia = None
    regime_selecionado = None
    com_kit_higiene = None

    ultima_data_atualizado = (
        Relacao.objects
        .exclude(atualizado__isnull=True)
        .aggregate(Max('atualizado')).get('atualizado__max')
    )

    #print(f'Ultima data atualizado: {ultima_data_atualizado}')
    
    ipen = request.GET.get('ipen')
    numero_rouparia = request.GET.get('numero_rouparia')
    escolha_tipo_regime = request.GET.get('escolha_tipo_regime')
    com_higiene = request.GET.get('com_higiene')

    # Usar o form alternativo que funciona melhor
    initial_data = {}
    
    if escolha_tipo_regime == 'on':
        initial_data['escolha_tipo_regime'] = True
        regime_selecionado = 'fechado'
    else:
        initial_data['escolha_tipo_regime'] = False
        regime_selecionado = 'semiaberto'
        
    if com_higiene == 'on':
        initial_data['com_higiene'] = True
        com_kit_higiene = True
    else:
        initial_data['com_higiene'] = False
        com_kit_higiene = False
    
    form = TermoRoupariaForm(initial=initial_data)
    
    # Busca o detento se IPEN foi fornecido
    if ipen:
        try:
            detento = Relacao.objects.get(IPEN=ipen)
        except Relacao.DoesNotExist:
            detento = None
    
    

    return render(request, 'gerador_rouparia.html', {
        'detento': detento,
        'numero_rouparia': numero_rouparia,
        'regime_selecionado': regime_selecionado,
        'com_kit_higiene': com_kit_higiene,
        'ultima_data_atualizado': ultima_data_atualizado,
        'form': form,
        'ano_corrente': ANO_CORRENTE,
    })

@checked_debug_decorador
def gerar_termo_rouparia(request, detento_id:int, numero_kit:int, regime:str, com_higiene:str):
    '''
    Gera e baixa um documento no formato PDF do termo de rouparia do detento
    Returns:
        FileResponse: Documento pdf para download
    
    Args:
        Request: ID do detento, numero do kit, regime (fechado ou semiaberto) e se inclui kit higiene    
    '''
    detento = get_object_or_404(Relacao, id=detento_id)
    
    # Determinar o tipo de regime baseado no parâmetro
    if regime == 'on' or regime == 'True' or regime == 'fechado':
        try:
            descricao_obj = Descricao_termo_rouparia.objects.first()
            descricao_rouparia = descricao_obj.descricao_fechado if descricao_obj else "Kit de rouparia padrão do regime fechado"
        except:
            descricao_rouparia = "ERRO"
    elif regime == 'off' or regime == 'False' or regime == 'semiaberto':
        try:
            descricao_obj = Descricao_termo_rouparia.objects.first()
            descricao_rouparia = descricao_obj.descricao_semiaberto if descricao_obj else "Kit de rouparia padrão do regime semiaberto"
        except:
            descricao_rouparia = "ERRO"
    else:
        descricao_rouparia = "ERRO"
    
    # Processar o valor do kit higiene
    if com_higiene == 'on' or com_higiene == 'True' or com_higiene == '1':
        incluir_higiene = True
    else:
        incluir_higiene = False
    
    # Criar PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2.5 * cm,
        leftMargin=2 * cm,
        topMargin=1.5 * cm,
        bottomMargin=2 * cm
    )

    # Estilos
    estilos = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle(
        name='Titulo',
        parent=estilos['Normal'],
        alignment=TA_CENTER,
        fontName='Arial-Bold',
        fontSize=14,
        leading=18,
        spaceAfter=20
    )

    estilo_subtitulo = ParagraphStyle(
        name='Subtitulo',
        parent=estilos['Normal'],
        alignment=TA_JUSTIFY,
        fontName='Arial-Bold',
        fontSize=12,
        leading=15,
        spaceAfter=12
    )

    estilo_justificado = ParagraphStyle(
        name='Justificado',
        parent=estilos['Normal'],
        alignment=TA_JUSTIFY,
        fontName='Arial',
        fontSize=11,
        leading=15,
        spaceAfter=12
    )

    estilo_centralizado = ParagraphStyle(
        name='Centralizado',
        parent=estilos['Normal'],
        alignment=TA_CENTER,
        fontName='Arial',
        fontSize=11,
        leading=15
    )

    descricao_kit_higiene = DescricaoKitHigiene.objects.first().descricao
    checked_data = DescricaoKitHigiene.objects.first().checked_data_recebido

    elementos = []
    elementos.append(Spacer(1, 1.5 * cm))
        
    # Título
    elementos.append(Paragraph("<b>TERMO DE RECEBIMENTO</b>", estilo_titulo))
    elementos.append(Spacer(1, 0.5 * cm))
    texto = "Instruções:"
    elementos.append(Paragraph(texto, estilo_subtitulo))

    texto = f" 01) Os internos devem assinar a opção com um X;<br/>02) Na opção \u201cobservação\u201d descrever o que está sendo entregue (tamanho e quantidade de uniforme);<br/>03) O termo de recebimento, devidamente assinado, deverá ser digitalizado e arquivado no IPEN do interno."
    elementos.append(Paragraph(texto, estilo_justificado))
        
    tabela_dados = []
    data_atual = timezone.now().strftime('%d/%m/%Y')

    tabela_dados.append([
        Paragraph("INTERNO:", estilo_justificado),
        Paragraph(f"{detento.nome}", estilo_subtitulo),
        "",
        ""
    ])

    tabela_dados.append([
        Paragraph("IPEN:", estilo_justificado),
        Paragraph(f"{detento.IPEN}", estilo_subtitulo),
        Paragraph(f"DATA: {data_atual}", estilo_justificado),
        ""
    ])

    if incluir_higiene:
        tabela_dados.append([
            Paragraph("X", estilo_centralizado),
            Paragraph("Kit higiene", estilo_justificado),
            "",
            ""
        ])
    else:
        tabela_dados.append([
            "",
            Paragraph("Kit higiene", estilo_justificado),
            "",
            ""
        ])

    tabela_dados.append([
        Paragraph("X", estilo_centralizado),
        Paragraph("Uniforme", estilo_justificado),
        "",
        ""
    ])

    tabela_dados.append([
        Paragraph("X", estilo_centralizado),
        Paragraph("Cobertor", estilo_justificado),
        "",
        ""
    ])

    tabela_dados.append([
        Paragraph("Observação:", estilo_subtitulo),
        "",
        "",
        ""
    ])

    tabela_dados.append([
        Paragraph("Se uniforme, quantidade e tamanho.", estilo_justificado),
        "",
        "",
        ""
    ])

    if incluir_higiene:
        tabela_dados.append([
            Paragraph(f"{descricao_rouparia}<br/> <br/>{descricao_kit_higiene}", estilo_justificado),
            "",
            "",
            ""
        ])
    else:
        tabela_dados.append([
            Paragraph(f"{descricao_rouparia}", estilo_justificado),
            "",
            "",
            ""
        ])

    tabela_dados.append([
        Paragraph(f"Kit número: {numero_kit}", estilo_justificado),
        "",
        "",
        ""
    ])

    col_widths = [3 * cm, 7 * cm, 3 * cm, 3 * cm]
    tabela = Table(tabela_dados, colWidths=col_widths, hAlign='LEFT')
    tabela.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('SPAN', (1, 0), (3, 0)),
        ('SPAN', (2, 1), (3, 1)),
        ('SPAN', (2, 0), (3, 0)),
        ('SPAN', (1, 2), (3, 2)),
        ('SPAN', (1, 3), (3, 3)),
        ('SPAN', (1, 4), (3, 4)),
        ('SPAN', (1, 5), (3, 5)),
        ('SPAN', (0, 6), (3, 6)),
        ('SPAN', (0, 7), (3, 7)),
        ('SPAN', (0, 8), (3, 8)),
    ]))

    elementos.append(tabela)
    elementos.append(Spacer(1, 1 * cm))
    
    if checked_data:
        elementos.append(Paragraph(f"Recebido em {data_atual}", estilo_justificado))
        elementos.append(Spacer(1, 0.75 * cm))
    else:
        elementos.append(Paragraph(f"Recebido em _____/_______/_______", estilo_justificado))
        elementos.append(Spacer(1, 0.75 * cm))

    elementos.append(Paragraph("_______________________________________", estilo_justificado))
    elementos.append(Paragraph(f"{detento.nome}", estilo_justificado))
    elementos.append(Spacer(1, 0.75 * cm))  

    elementos.append(Paragraph("_______________________________________", estilo_justificado))
    elementos.append(Paragraph(f"Assinatura do servidor (nome completo)", estilo_justificado))
    elementos.append(Spacer(1, 0.75 * cm))
    
    # Gerar a página 1 (Termo de Rouparia)
    doc.build(elementos, onFirstPage=cabecalho_e_rodape, onLaterPages=cabecalho_e_rodape)

    # Se incluir higiene, adicionar a página 2 com o Memorando Penal
    if incluir_higiene:
        buffer.seek(0)
        buffer_final = _adicionar_memorando_penal(buffer, detento)
    else:
        buffer_final = buffer

    buffer_final.seek(0)
    nome_arquivo = f'termo_rouparia_{detento.nome}_{numero_kit}.pdf'
    response = HttpResponse(buffer_final.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{nome_arquivo}"'
    return response

def _get_mes_referencia():
    """Retorna o mês de referência bimestral e o mês corrente."""
    hoje = datetime.datetime.now()
    mes = hoje.month
    meses_ref = {
        1: ("jan./fev.", "janeiro"),
        2: ("jan./fev.", "fevereiro"),
        3: ("março/abril", "março"),
        4: ("março/abril", "abril"),
        5: ("maio/junho", "maio"),
        6: ("maio/junho", "junho"),
        7: ("julho/agosto", "julho"),
        8: ("julho/agosto", "agosto"),
        9: ("set./out.", "setembro"),
        10: ("set./out.", "outubro"),
        11: ("nov./dez.", "novembro"),
        12: ("nov./dez.", "dezembro"),
    }
    return meses_ref.get(mes, ("", ""))


def _encurtar_nome(nome_completo, limite=33):
    """Encurta o nome mantendo primeiro e último, abreviando os do meio."""
    if len(nome_completo) <= limite:
        return nome_completo
    partes = nome_completo.split()
    if len(partes) <= 2:
        return nome_completo
    primeiro = partes[0]
    ultimo = partes[-1]
    meio = [p if len(p) <= 3 else p[0] + "." for p in partes[1:-1]]
    return " ".join([primeiro] + meio + [ultimo])


def _adicionar_memorando_penal(buffer_termo, detento):
    """
    Recebe o buffer do PDF do termo de rouparia (página 1) e adiciona
    a página 2 com o Memorando Penal no estilo do Memorando_Penal.py original.
    Layout: A4 retrato com conteúdo rotacionado 90° (paisagem visual).
    Retorna um novo buffer com ambas as páginas.
    """

    # Ler o PDF do termo (página 1)
    reader = PdfReader(buffer_termo)
    writer = PdfWriter()
    
    # Adicionar página(s) do termo de rouparia
    for page in reader.pages:
        writer.add_page(page)

    # Criar página 2 (memorando penal) — A4 retrato com rotate(90)
    buffer_memo = io.BytesIO()
    page_size = A4  # 595.28 x 841.89

    c = canvas.Canvas(buffer_memo, pagesize=page_size)
    c.setTitle("Memorando de apenado")

    nome_interno = _encurtar_nome(detento.nome)
    numero_ipen = str(detento.IPEN)
    mes_referencia, mes_corrente = _get_mes_referencia()

    # Caminho da logo
    caminho_logo = os.path.join(settings.BASE_DIR, 'staticfiles', 'img', 'logo3.png')

    c.setStrokeColorRGB(0, 0, 0, 0.7)
    c.setLineWidth(0.5)
    c.setFillColor("black")

    # ==========================================
    # PRIMEIRO MEMORANDO (metade superior da folha)
    # ==========================================

    # Cabeçalho
    c.setFont("Helvetica-Oblique", 11, leading=1)
    c.rotate(90)
    if os.path.exists(caminho_logo):
        c.drawImage(caminho_logo, 15 * cm, -3 * cm, width=2 * cm, height=2 * cm, mask='auto')
    c.drawString(17.5 * cm, -1.5 * cm, "ESTADO DE SANTA CATARINA")
    c.setFont("Helvetica-Oblique", 8, leading=1)
    c.drawString(17.5 * cm, -1.9 * cm, "SECRETARIA DE ESTADO DE JUSTIÇA E REINTEGRAÇÃO SOCIAL")
    c.drawString(17.5 * cm, -2.3 * cm, "PRESÍDIO REGIONAL DE MARAVILHA")
    c.rotate(270)

    # Componente ESCRITA (linhas para escrever)
    for i in range(12):
        c.rect((7 + i) * cm, 15 * cm, 1 * cm, 14.3 * cm, fill=0)

    # Componente assinatura e data
    c.rect(19.5 * cm, 15 * cm, 1 * cm, 14.3 * cm, fill=0)
    c.rect(19.5 * cm, 15 * cm, 1 * cm, 3 * cm, fill=0)
    c.rotate(90)
    c.setFont("Helvetica-Oblique", 8, leading=1)
    c.drawString(15 * cm, -19.3 * cm, "APENADO")
    c.drawCentredString(15.5 * cm, -19.8 * cm, "DATA")
    c.drawCentredString(19 * cm, -19.8 * cm, "ASSINATURA")
    c.rotate(270)

    # Componente Nome e Matrícula
    c.rect(4.8 * cm, 15 * cm, 1 * cm, 14.3 * cm, fill=0)  # ao setor
    c.rect(3.5 * cm, 15 * cm, 1 * cm, 11 * cm, fill=0)     # NOME
    c.rect(3.5 * cm, 26 * cm, 1 * cm, 3.3 * cm)             # Matricula
    c.rect(2.5 * cm, 26 * cm, 1 * cm, 3.3 * cm, fill=0)     # período
    c.setFont("Helvetica-Oblique", 8, leading=1)
    c.rotate(90)
    c.drawString(15.5 * cm, -3.8 * cm, "NOME")
    c.drawString(26.2 * cm, -3.8 * cm, "MATRÍCULA")
    c.setFont("Helvetica-Oblique", 14, leading=1)
    c.drawCentredString(20 * cm, -4.3 * cm, f"{nome_interno}")
    c.drawRightString(28.5 * cm, -4.3 * cm, f"{numero_ipen}")
    c.drawCentredString(27.5 * cm, -3.3 * cm, f"{mes_corrente}")
    c.setFont("Helvetica-Oblique", 12, leading=1)
    c.drawRightString(25.8 * cm, -3.3 * cm, "MEMORANDO DE APENADO")
    c.rotate(270)

    # Componente AO SETOR
    c.rect(4.8 * cm, 15 * cm, 2 * cm, 14.3 * cm, fill=0)
    c.setFont("Helvetica-Oblique", 8, leading=1)
    c.rotate(90)
    c.drawString(15.8 * cm, -5.2 * cm, "AO SETOR")
    c.setFont("Helvetica-Oblique", 12, leading=1)
    c.drawString(15.8 * cm, -5.6 * cm, "(  )PSICÓLOGA; (  )DIRETOR; (  )PECÚLIO; (  )EDUCAÇÃO;")
    c.drawString(15.7 * cm, -6.6 * cm, "(  )SOCIAL; (  )CHEFE DE SEGURANÇA e (  )OUTROS:__________")
    c.rotate(270)

    # ==========================================
    # SEGUNDO MEMORANDO (metade inferior) — PENAL
    # ==========================================

    # Cabeçalho
    c.setFont("Helvetica-Oblique", 11, leading=1)
    c.rotate(90)
    if os.path.exists(caminho_logo):
        c.drawImage(caminho_logo, 0.2 * cm, -3 * cm, width=2 * cm, height=2 * cm, mask='auto')
    c.drawString(2.5 * cm, -1.5 * cm, "ESTADO DE SANTA CATARINA")
    c.setFont("Helvetica-Oblique", 8, leading=1)
    c.drawString(2.5 * cm, -1.9 * cm, "SECRETARIA DE ESTADO DE JUSTIÇA E REINTEGRAÇÃO SOCIAL")
    c.drawString(2.5 * cm, -2.3 * cm, "PRESÍDIO REGIONAL DE MARAVILHA")
    c.rotate(270)

    # Componente Nome e Matrícula
    c.rect(3.5 * cm, 0.2 * cm, 1 * cm, 14.3 * cm, fill=0)
    c.rect(3.5 * cm, 0.2 * cm, 1 * cm, 11 * cm, fill=0)
    c.rect(2.5 * cm, 11.2 * cm, 1 * cm, 3.3 * cm, fill=0)   # período
    c.setFont("Helvetica-Oblique", 8, leading=1)
    c.rotate(90)
    c.drawString(0.8 * cm, -3.8 * cm, "NOME")
    c.drawString(11.5 * cm, -3.8 * cm, "MATRÍCULA")
    c.setFont("Helvetica-Oblique", 14, leading=1)
    c.drawCentredString(6 * cm, -4.3 * cm, f"{nome_interno}")
    c.drawRightString(14.3 * cm, -4.3 * cm, f"{numero_ipen}")
    c.drawCentredString(12.8 * cm, -3.3 * cm, f"{mes_referencia}")
    c.setFont("Helvetica-Oblique", 12, leading=1)
    c.drawRightString(11 * cm, -3.3 * cm, "MEMORANDO DE APENADO")
    c.rotate(270)

    # Componente AO SETOR — PENAL
    c.rect(4.8 * cm, 0.2 * cm, 1 * cm, 14.3 * cm, fill=0)
    c.setFont("Helvetica-Oblique", 8, leading=1)
    c.rotate(90)
    c.drawString(0.8 * cm, -5.2 * cm, "AO SETOR")
    c.setFont("Helvetica-Oblique", 14.3, leading=1)
    c.drawCentredString(7 * cm, -5.5 * cm, "PENAL")
    c.rotate(270)

    # Componente ESCRITA (linhas para escrever) — PENAL
    for i in range(13):
        c.rect((6 + i) * cm, 0.2 * cm, 1 * cm, 14.3 * cm, fill=0)

    # Componente data e assinatura — PENAL
    c.rect(19.5 * cm, 0.2 * cm, 1 * cm, 14.3 * cm, fill=0)
    c.rect(19.5 * cm, 0.2 * cm, 1 * cm, 3 * cm, fill=0)
    c.rotate(90)
    c.setFont("Helvetica-Oblique", 8, leading=1)
    c.drawString(0.2 * cm, -19.3 * cm, "APENADO")
    c.drawCentredString(0.8 * cm, -19.8 * cm, "DATA")
    c.drawCentredString(4.2 * cm, -19.8 * cm, "ASSINATURA")
    c.rotate(270)

    c.showPage()
    c.save()

    # Combinar os dois PDFs (termo + memorando)
    buffer_memo.seek(0)
    reader_memo = PdfReader(buffer_memo)
    
    for page in reader_memo.pages:
        writer.add_page(page)

    buffer_final = io.BytesIO()
    writer.write(buffer_final)
    
    return buffer_final

@checked_debug_decorador
def view_termo_autorizacao(request, relacao_id):
    """
    Visualiza o termo de autorização de trabalho do detento.
    """
    relacao = Relacao.objects.get(id=relacao_id)
    if not relacao.trampo_empresa:
        return render(request, 'termo_autorizacao.html', {
            'error': 'Nenhum termo de autorização encontrado para este detento.'
        })
    
    return render(request, 'termo_autorizacao.html', {
        'relacao': relacao,
        'empresa': relacao.trampo_empresa
    })


@checked_debug_decorador
def cadastro_trampo_view(request):
    detento = None
    empresa_conveniada_nome = None
    ipen = request.GET.get('ipen')
    empresa_conveniada = request.GET.get('empresa_conveniada')
    
    # Busca o detento se IPEN foi fornecido
    if ipen:
        try:
            detento = Relacao.objects.get(IPEN=ipen)
        except Relacao.DoesNotExist:
            detento = None
    
    # Busca o nome da empresa conveniada se foi selecionada
    if empresa_conveniada:
        empresas_dict = dict(Relacao.empresas_conveniadas)
        empresa_conveniada_nome = empresas_dict.get(empresa_conveniada, empresa_conveniada)
    
    return render(request, 'cadastro_trampo.html', {
        'detento': detento, 
        'empresa_conveniada': empresa_conveniada,
        'empresa_conveniada_nome': empresa_conveniada_nome,
        'empresas_conveniadas': Relacao.empresas_conveniadas, 
        'ano_corrente': ANO_CORRENTE,
    })


def _gerar_lote_kit_higiene(dados_lote):
    """
    Gera um PDF parcial para um lote de detentos (executado em processo separado).
    Recebe um dict com os dados serializados (sem objetos Django).
    Retorna bytes do PDF gerado.
    """
    # Re-registrar fontes no subprocesso
    arial_path = dados_lote['arial_path']
    arial_bold_path = dados_lote['arial_bold_path']
    
    try:
        pdfmetrics.getFont('Arial')
    except:
        pdfmetrics.registerFont(TTFont('Arial', arial_path))
        pdfmetrics.registerFont(TTFont('Arial-Bold', arial_bold_path))

    detentos_data = dados_lote['detentos']
    descricao_kit_higiene = dados_lote['descricao_kit_higiene']
    checked_data = dados_lote['checked_data']
    checked_kit = dados_lote['checked_kit']
    data_atual = dados_lote['data_atual']
    caminho_logo = dados_lote['caminho_logo']
    logo_existe = dados_lote['logo_existe']

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2.5 * cm,
        leftMargin=2 * cm,
        topMargin=1.5 * cm,
        bottomMargin=2 * cm
    )

    estilos = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle(
        name='Titulo', parent=estilos['Normal'],
        alignment=TA_CENTER, fontName='Arial-Bold',
        fontSize=14, leading=18, spaceAfter=20
    )
    estilo_subtitulo = ParagraphStyle(
        name='Subtitulo', parent=estilos['Normal'],
        alignment=TA_JUSTIFY, fontName='Arial-Bold',
        fontSize=12, leading=15, spaceAfter=12
    )
    estilo_justificado = ParagraphStyle(
        name='Justificado', parent=estilos['Normal'],
        alignment=TA_JUSTIFY, fontName='Arial',
        fontSize=11, leading=15, spaceAfter=12
    )
    estilo_centralizado = ParagraphStyle(
        name='Centralizado', parent=estilos['Normal'],
        alignment=TA_CENTER, fontName='Arial',
        fontSize=11, leading=15
    )

    # Elementos estáticos reutilizáveis
    p_kit_higiene = Paragraph("Kit higiene", estilo_justificado)
    p_uniforme = Paragraph("Uniforme", estilo_justificado)
    p_cobertor = Paragraph("Cobertor", estilo_justificado)
    p_observacao = Paragraph("Observação:", estilo_subtitulo)
    p_se_uniforme = Paragraph("Se uniforme, quantidade e tamanho.", estilo_justificado)
    p_descricao_kit = Paragraph(f"{descricao_kit_higiene}", estilo_justificado)
    p_x = Paragraph("X", estilo_centralizado)
    p_espaco = Paragraph(" ", estilo_centralizado)
    p_assinatura_servidor = Paragraph("Assinatura do servidor (nome completo)", estilo_justificado)
    p_linha = Paragraph("_______________________________________", estilo_justificado)

    if checked_data:
        p_recebido = Paragraph(f"Recebido em {data_atual}", estilo_justificado)
    else:
        p_recebido = Paragraph("Recebido em _____/_______/_______", estilo_justificado)

    col_widths = [3 * cm, 7 * cm, 3 * cm, 3 * cm]
    estilo_tabela = TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('SPAN', (1, 0), (3, 0)),
        ('SPAN', (2, 1), (3, 1)),
        ('SPAN', (2, 0), (3, 0)),
        ('SPAN', (1, 2), (3, 2)),
        ('SPAN', (1, 3), (3, 3)),
        ('SPAN', (1, 4), (3, 4)),
        ('SPAN', (1, 5), (3, 5)),
        ('SPAN', (0, 6), (3, 6)),
        ('SPAN', (0, 7), (3, 7)),
    ])

    texto_instrucoes = ' 01) Os internos devem assinar a opção com um X;<br/>02) Na opção \u201cobservação\u201d descrever o que está sendo entregue (tamanho e quantidade de uniforme); <br/> 03) O termo de recebimento, devidamente assinado, deverá ser digitalizado e arquivado no IPEN do interno.'

    spacer_1_5 = Spacer(1, 1.5 * cm)
    spacer_0_5 = Spacer(1, 0.5 * cm)
    spacer_1 = Spacer(1, 1 * cm)
    spacer_0_75 = Spacer(1, 0.75 * cm)

    elementos = []
    total = len(detentos_data)

    for i, det in enumerate(detentos_data):
        elementos.append(spacer_1_5)
        elementos.append(Paragraph("<b>TERMO DE RECEBIMENTO</b>", estilo_titulo))
        elementos.append(spacer_0_5)
        elementos.append(Paragraph("Instruções:", estilo_subtitulo))
        elementos.append(Paragraph(texto_instrucoes, estilo_justificado))

        tabela_dados = [
            [Paragraph("INTERNO:", estilo_justificado), Paragraph(det['nome'], estilo_justificado), "", ""],
            [Paragraph("IPEN:", estilo_justificado), Paragraph(str(det['IPEN']), estilo_justificado),
             Paragraph(f"DATA: {data_atual}", estilo_justificado), ""],
            [p_x if checked_kit else "", p_kit_higiene, "", ""],
            [p_espaco, p_uniforme, "", ""],
            ["", p_cobertor, "", ""],
            [p_observacao, "", "", ""],
            [p_se_uniforme, "", "", ""],
            [p_descricao_kit, "", "", ""],
        ]

        tabela = Table(tabela_dados, colWidths=col_widths, hAlign='LEFT')
        tabela.setStyle(estilo_tabela)

        elementos.append(tabela)
        elementos.append(spacer_1)
        elementos.append(p_recebido)
        elementos.append(spacer_0_75)
        elementos.append(p_linha)
        elementos.append(Paragraph(det['nome'], estilo_justificado))
        elementos.append(spacer_0_75)
        elementos.append(p_linha)
        elementos.append(p_assinatura_servidor)
        elementos.append(spacer_0_75)

        if i < total - 1:
            elementos.append(PageBreak())

    def _cabecalho_rodape_worker(canvas_obj, doc_obj):
        canvas_obj.saveState()
        if logo_existe:
            logo = ImageReader(caminho_logo)
            canvas_obj.drawImage(logo, x=doc_obj.leftMargin, y=A4[1] - 3.2 * cm,
                                  width=2 * cm, height=2.5 * cm, mask='auto')
        canvas_obj.setFont("Helvetica", 9)
        x_texto = doc_obj.leftMargin + 2.3 * cm
        y_topo = A4[1] - 1.2 * cm
        linhas = [
            "ESTADO DE SANTA CATARINA",
            "SECRETARIA DE ESTADO DE JUSTIÇA E REINTEGRAÇÃO SOCIAL",
            "DEPARTAMENTO DE POLÍCIA PENAL",
            "PRESÍDIO REGIONAL DE MARAVILHA",
            ""
        ]
        for idx, linha in enumerate(linhas):
            canvas_obj.drawString(x_texto, y_topo - idx * 0.4 * cm, linha)
        canvas_obj.setFont("Helvetica-Oblique", 9)
        canvas_obj.setFillColor(colors.grey)
        canvas_obj.drawCentredString(doc_obj.pagesize[0] / 2, 2.1 * cm, "POLÍCIA PENAL DE SANTA CATARINA")
        canvas_obj.drawCentredString(doc_obj.pagesize[0] / 2, 1.7 * cm, "Presídio Regional de Maravilha")
        canvas_obj.drawCentredString(doc_obj.pagesize[0] / 2, 1.3 * cm,
                                      "Avenida Sul Brasil, 1607, Novo Bairro, Maravilha/SC - CEP 89874-000")
        canvas_obj.drawCentredString(doc_obj.pagesize[0] / 2, 0.9 * cm,
                                      "Telefone: (49) 3664-6672 / pr29@pp.sc.gov.br")
        canvas_obj.restoreState()

    doc.build(elementos, onFirstPage=_cabecalho_rodape_worker, onLaterPages=_cabecalho_rodape_worker)

    buffer.seek(0)
    return buffer.read()


def _combinar_pdfs(lista_bytes_pdfs):
    """Combina múltiplos PDFs (em bytes) em um único buffer."""
    writer = PdfWriter()
    for pdf_bytes in lista_bytes_pdfs:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        for page in reader.pages:
            writer.add_page(page)
    buffer_final = io.BytesIO()
    writer.write(buffer_final)
    return buffer_final


@checked_debug_decorador
def gerar_termo_kit_higiene(request):
    detentos = list(
        Relacao.objects
        .filter(local_galeria__in=['A', 'B', 'C', 'D', 'E'])
        .only('IPEN', 'nome', 'local_alocacao', 'local_residencia', 'local_galeria')
        .order_by('local_galeria', 'local_residencia', 'nome')
    )
    if not detentos:
        return HttpResponse(
            "Erro: Nenhum detento encontrado nas galerias A, B, C, D ou E.",
            content_type='text/plain',
            status=400
        )

    # Buscar configurações UMA VEZ
    config_higiene = DescricaoKitHigiene.objects.first()
    if config_higiene is None:
        return HttpResponse(
            "Erro: Nenhuma descrição de kit de higiene cadastrada. "
            "Cadastre pelo menos um registro em 'Descrições do kit de higiene' no admin.",
            content_type='text/plain',
            status=400
        )
    descricao_kit_higiene = config_higiene.descricao
    checked_data = config_higiene.checked_data_recebido
    checked_kit = config_higiene.checked_kit_higiene
    data_atual = timezone.now().strftime('%d/%m/%Y')

    caminho_logo = os.path.join(settings.BASE_DIR, 'staticfiles', 'img', 'logo.png')
    logo_existe = os.path.exists(caminho_logo)

    # Serializar detentos (objetos Django não podem ir para subprocessos)
    detentos_serializados = [{'IPEN': d.IPEN, 'nome': d.nome} for d in detentos]

    # Determinar número de workers (núcleos disponíveis)
    num_cpus = os.cpu_count() or 2
    num_workers = min(num_cpus, 4)  # Limitar a 4 workers

    total = len(detentos_serializados)
    tamanho_lote = max(1, math.ceil(total / num_workers))

    # Dividir em lotes
    lotes = []
    for inicio in range(0, total, tamanho_lote):
        lote = detentos_serializados[inicio:inicio + tamanho_lote]
        lotes.append({
            'detentos': lote,
            'descricao_kit_higiene': descricao_kit_higiene,
            'checked_data': checked_data,
            'checked_kit': checked_kit,
            'data_atual': data_atual,
            'caminho_logo': caminho_logo,
            'logo_existe': logo_existe,
            'arial_path': arial_path,
            'arial_bold_path': arial_bold_path,
        })

    if len(lotes) <= 1:
        # Poucos detentos, não vale paralelizar
        pdf_bytes = _gerar_lote_kit_higiene(lotes[0])
        buffer_final = io.BytesIO(pdf_bytes)
    else:
        # Paralelizar com ProcessPoolExecutor
        resultados_ordenados = [None] * len(lotes)
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            futuros = {}
            for idx, lote in enumerate(lotes):
                futuro = executor.submit(_gerar_lote_kit_higiene, lote)
                futuros[futuro] = idx

            for futuro in as_completed(futuros):
                idx = futuros[futuro]
                resultados_ordenados[idx] = futuro.result()

        # Combinar PDFs na ordem correta
        buffer_final = _combinar_pdfs(resultados_ordenados)

    buffer_final.seek(0)
    response = HttpResponse(buffer_final.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="kit_higiene_{datetime.date.today()}.pdf"'
    return response

@checked_debug_decorador
def gerar_termo_autorizacao(request, detento_id, empresa_conveniada):
    # Busca o detento no banco de dados
    detento = get_object_or_404(Relacao, id=detento_id)

    # Busca o nome completo da empresa
    empresas_dict = dict(Relacao.empresas_conveniadas)
    empresa_nome = empresas_dict.get(empresa_conveniada, empresa_conveniada)
    
    # Se não foi passada empresa pela URL, usa a do detento
    if empresa_conveniada == "Não informada" or not empresa_conveniada:
        if hasattr(detento, 'trampo_empresa') and detento.trampo_empresa:
            empresa_nome = detento.get_trampo_empresa_display()
        else:
            empresa_nome = "Empresa não informada"

    # Criar novo PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2.5 * cm,
        leftMargin=2 * cm,
        topMargin=1.5 * cm,
        bottomMargin=2 * cm
    )

    # Estilos
    estilos = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle(
        name='Titulo',
        parent=estilos['Normal'],
        alignment=TA_CENTER,
        fontName='Arial-Bold',
        fontSize=12,
        leading=15,
        spaceAfter=20
    )
    
    estilo_justificado = ParagraphStyle(
        name='Justificado',
        parent=estilos['Normal'],
        alignment=TA_JUSTIFY,
        firstLineIndent=1.5 * cm,
        fontName='Arial',
        fontSize=11,
        leading=15,
        spaceAfter=12
    )

    estilo_centralizado = ParagraphStyle(
        name='Centralizado',
        parent=estilos['Normal'],
        alignment=TA_CENTER,
        fontName='Arial',
        fontSize=11,
        leading=15
    )

    elementos = []

    # Espaço do cabeçalho
    elementos.append(Spacer(1, 2 * cm))

    # Título
    elementos.append(Paragraph("<b>Termo de autorização e ciência das condições para ingresso no trabalho</b>", estilo_titulo))
    elementos.append(Spacer(1, 0.5 * cm))

    # Parágrafo 1
    paragrafo1 = f"""No Presídio Regional de Maravilha, nesta data, o interno <b> {detento.nome} </b> - <b> {detento.IPEN} </b>, 
    participou de instrução e ciência dos termos e condições para ingresso no trabalho externo junto à Empresa <b> {empresa_nome} </b>, 
    na qual passará trabalhar."""
    elementos.append(Paragraph(paragrafo1, estilo_justificado))

    # Parágrafo 2
    paragrafo2 = """Neste ato, foi informado ao apenado que a prestação de trabalho externo, a ser autorizada pela direção do estabelecimento, 
    dependerá de aptidão, disciplina e responsabilidade (art. 37 da LEP), e que revogar-se-á a autorização de trabalho externo ao preso 
    que vier a praticar fato definido como crime, for punido por falta grave, ou tiver comportamento contrário aos requisitos 
    (parágrafo único do art. 37 da LEP)."""
    elementos.append(Paragraph(paragrafo2, estilo_justificado))

    # Parágrafo 3
    paragrafo3 = """O interno foi informado das condições do trabalho e necessidade de disciplina que consiste na colaboração com a ordem, 
    na obediência às determinações das autoridades e seus agentes e no desempenho do trabalho (art. 44 da LEP). Nos termos do artigo 39, 
    II e V foi cientificado ainda que é um dever a obediência ao servidor e respeito a qualquer pessoa com quem deva relacionar-se 
    bem como a execução do trabalho, das tarefas e das ordens recebidas de forma geral."""
    elementos.append(Paragraph(paragrafo3, estilo_justificado))

    # Parágrafo 4
    paragrafo4 = """Dentre as ordens recebidas, destaca-se a impossibilidade de retirar-se do local de trabalho sem autorização de sua chefia 
    ou encarregado imediato ou geral, permanecer no refeitório sob vigilância da pessoa responsável durante e após o almoço até o horário 
    de começar a trabalhar, a impossibilidade de ingerir qualquer tipo de bebida alcoólica, o uso de qualquer telefone fixo ou móvel 
    para contato externo, bem como acesso a redes sociais como facebook, twitter, x etc., não manter contato com pessoas que nada tenham 
    relação com o trabalho para o qual foi autorizado e outras situações similares."""
    elementos.append(Paragraph(paragrafo4, estilo_justificado))

    # Parágrafo 5
    paragrafo5 = """Nos termos do art. 36, § 3º da LEP, declaro que aceito as condições impostas acima e mediante minha assinatura, 
    concordo com a prestação de trabalho em entidade privada, consentimento expresso que faço abaixo, mediante o Diretor do estabelecimento 
    penal que atesta ser ato voluntário e de meu interesse."""
    elementos.append(Paragraph(paragrafo5, estilo_justificado))

    # Parágrafo 6
    paragrafo6 = """Esse termo não isenta o interno das obrigações dispostas em lei ou outras necessidades ou faltas que possa cometer 
    que não estejam aqui expressas."""
    elementos.append(Paragraph(paragrafo6, estilo_justificado))

    elementos.append(Spacer(1, 1 * cm))

    # Data
    data_atual = timezone.now().strftime('%d de %B de %Y')
    elementos.append(Paragraph(f"Maravilha, {data_atual}.", estilo_centralizado))
    elementos.append(Spacer(1, 2 * cm))

    # Assinatura
    elementos.append(Paragraph("_______________________________________", estilo_centralizado))
    elementos.append(Paragraph(f"<b> {detento.nome} </b>", estilo_centralizado))

    # Gerar o PDF
    doc.build(elementos, onFirstPage=cabecalho_e_rodape, onLaterPages=cabecalho_e_rodape)

    buffer.seek(0)
    nome_arquivo = f'termo_autorizacao_{detento.nome}.pdf'
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{nome_arquivo}"'
    return response

def cabecalho_e_rodape(canvas, doc):
    
   

    # Cabeçalho
    canvas.saveState()

    # Caminho da logo
    caminho_logo = os.path.join(settings.BASE_DIR, 'staticfiles', 'img', 'logo.png')
    if os.path.exists(caminho_logo):
        logo = ImageReader(caminho_logo)
        canvas.drawImage(logo, x=doc.leftMargin, y=A4[1] - 3.2*cm, width=2*cm, height=2.5*cm, mask='auto')

    # Texto institucional (centralizado à direita da logo)
    canvas.setFont("Helvetica", 9)
    x_texto = doc.leftMargin + 2.3 * cm
    y_topo = A4[1] - 1.2 * cm

    linhas = [
        "ESTADO DE SANTA CATARINA",
        "SECRETARIA DE ESTADO DE JUSTIÇA E REINTEGRAÇÃO SOCIAL",
        "DEPARTAMENTO DE POLÍCIA PENAL",
        "PRESÍDIO REGIONAL DE MARAVILHA",
        ""
    ]
    for i, linha in enumerate(linhas):
        canvas.drawString(x_texto, y_topo - i * 0.4 * cm, linha)

    # Rodapé
    canvas.setFont("Helvetica-Oblique", 9)
    canvas.setFillColor(colors.grey)
    canvas.drawCentredString(
        x=doc.pagesize[0] / 2,
        y=2.1 * cm,
        text="POLÍCIA PENAL DE SANTA CATARINA"
    )
    canvas.drawCentredString(
        x=doc.pagesize[0] / 2,
        y=1.7 * cm,
        text="Presídio Regional de Maravilha"
    )
    canvas.drawCentredString(
        x=doc.pagesize[0] / 2,
        y=1.3 * cm,
        text="Avenida Sul Brasil, 1607, Novo Bairro, Maravilha/SC - CEP 89874-000"
    )
    canvas.drawCentredString(
        x=doc.pagesize[0] / 2,
        y=0.9 * cm,
        text="Telefone: (49) 3664-6672 / pr29@pp.sc.gov.br"
    )

    canvas.restoreState()

def cabecalho_e_rodape_ume(canvas, doc):
    
   

    # Cabeçalho
    canvas.saveState()

    # Caminho da logo
    caminho_logo = os.path.join(settings.BASE_DIR, 'staticfiles', 'img', 'logo.png')
    if os.path.exists(caminho_logo):
        logo = ImageReader(caminho_logo)
        canvas.drawImage(logo, x=doc.leftMargin, y=A4[1] - 3*cm, width=2*cm, height=2.5*cm, mask='auto')

    # Texto institucional (centralizado à direita da logo)
    canvas.setFont("Helvetica-Bold", 9)
    x_texto = doc.leftMargin + 2.3 * cm
    y_topo = A4[1] - 1.2 * cm

    linhas = [
        "ESTADO DE SANTA CATARINA",
        "SECRETARIA DE ESTADO DE JUSTIÇA E REINTEGRAÇÃO SOCIAL",
        "DEPARTAMENTO DE POLÍCIA PENAL",
        "UNIDADE DE MONITORAMENTO ELETRÔNICO - UME",
        " "
    ]
    for i, linha in enumerate(linhas):
        canvas.drawString(x_texto, y_topo - i * 0.4 * cm, linha)

    # Rodapé
    canvas.setFont("Helvetica-Oblique", 9)
    canvas.setFillColor(colors.grey)
    canvas.drawCentredString(
        x=doc.pagesize[0] / 2,
        y=1.5 * cm,
        text="UNIDADE DE MONITORAMENTO ELETRÔNICO"
    )
    canvas.drawCentredString(
        x=doc.pagesize[0] / 2,
        y=1.1 * cm,
        text="Rua Fúlvio Aducci, 1214, Estreito, Florianópolis/SC - CEP 88075-145"
    )
    canvas.drawCentredString(
        x=doc.pagesize[0] / 2,
        y=0.7 * cm,
        text="Tel: (48) 3665-7323 / (48) 3665-7327 / monitoramento@pp.sc.gov.br"
    )

    canvas.restoreState()

def termo_monitorado(request, detento_ipen):
    """
    Gera o termo de monitoramento eletrônico conforme o modelo
    '2 - TERMO DE MONITORAMENTO ATUALIZADO 27.05.2024.pdf'.
    """
    IPEN = detento_ipen
    detento = get_object_or_404(Relacao, IPEN=IPEN)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2.5 * cm,
        leftMargin=2 * cm,
        topMargin=1.5 * cm,
        bottomMargin=2 * cm
    )

    # Crie um estilo justificado para os parágrafos
    estilos = getSampleStyleSheet()
    estilo_justificado = ParagraphStyle(
        name='Justificado',
        parent=estilos['Normal'],
        alignment=TA_JUSTIFY,
        firstLineIndent=1.5 * cm,
        fontName='Arial',         # Altere para a fonte desejada, ex: 'Times-Roman', 'Courier', Arial
        fontSize=11,                  # Altere para o tamanho desejado
        leading=15,                   # Espaçamento entre linhas (opcional)
    )
    estilo_titulo = ParagraphStyle(
        name='Centralizado',
        parent=estilos['Normal'],
        alignment=TA_CENTER,
        fontName='Arial',    # Fonte para o título
        fontSize=11,                  # Tamanho do título
        leading=15,                   # Espaçamento entre linhas (opcional)
    )
    estilo_centralizado = ParagraphStyle(
        name='centralizado',
        parent=estilos['Normal'],
        alignment=TA_CENTER,
        fontName='Arial',
        fontSize=11,
        leading=15,
    )
    estilo_normal = ParagraphStyle(
        name='Normal',
        parent=estilos['Normal'],
        fontName='Arial',
        fontSize=11,
        leading=15,
    )


    elementos = []


    elementos.append(Spacer(1, 2 * cm))
    # Título centralizado
    elementos.append(Paragraph("<b>TERMO DE MONITORAMENTO ELETRÔNICO E DE INSTRUÇÕES AO MONITORADO PARA O USO DA TORNOZELEIRA ELETRÔNICA.</b>", estilo_titulo))
    elementos.append(Spacer(1, 0.5 * cm))

    

    # Corpo do termo conforme modelo atualizado
    elementos.append(Paragraph(
        f"Eu, {detento.nome} ({detento.IPEN}), declaro para os devidos fins, que fui devidamente instruído sobre o uso e conservação da TORNOZELEIRA ELETRÔNICA, e observarei, principalmente, o seguinte: carregamento diário por, no mínimo, <b>3 (TRÊS) horas, não utilizando extensões, benjamins, adaptadores ou similares, não recarregar durante o sono </b>, não retirar, queimar, abrir, forçar, danificar ou inutilizar o equipamento e/ou o carregador que acompanha, não praticar esporte de contato, não mergulhar com o equipamento em piscina, mar ou rio. A pessoa monitorada deverá zelar pelo dispositivo sendo responsável onerosamente pelos danos causados, em todo ou em parte, dos equipamentos de monitoramento.", estilo_justificado))
    elementos.append(Spacer(1, 0.2 * cm))
       
    elementos.append(Paragraph("Ainda, fui orientado(a) que, em casos de dúvidas, informações, acidente ou anomalia com o dispositivo, carregadores ou acessórios, devo entrar em contato com a Unidade de Monitoramento Eletrônico através dos números de telefones <b>(48) 3665-7322 / (48) 3665-7323 / (48) 3665- 7325 / (48) 3665-7327</b>, que funcionam 24 horas, como também informar à Unidade de Monitoramento Eletrônico qualquer necessidade de saída da área, ciente de que sem autorização judicial cometerei violação das regras de monitoramento, obedecendo <b>IMEDIATAMENTE AS ORIENTAÇÕES EMANADAS PELA UNIDADE DE MONITORAMENTO ELETRÔNICO – UME.</b>", estilo_justificado))
    elementos.append(Spacer(1, 0.2 * cm))

    elementos.append(Paragraph(
        "Tenho conhecimento das regras impostas na Decisão Judicial que concedeu o uso do monitoramento eletrônico e <b>DEVO RESPEITAR INTEGRALMENTE</b> o que foi determinado, bem como respeitar as instruções de uso do dispositivo, além de <b>fornecer número de telefone válido</b> e em funcionamento, juntamente com o endereço, mantendo esses atualizados. Sempre atender aos contatos que a Unidade de Monitoramento Eletrônico necessitar realizar e que ao fim do monitoramento eletrônico devo devolver a tornozeleira e seu carregador, que estão sob minha responsabilidade, em perfeito estado de conservação.", estilo_justificado))
    elementos.append(Spacer(1, 0.2 * cm))

    elementos.append(Paragraph(
        "Por fim, declaro estar ciente de todas as regras e condições a mim impostas e que estarei sujeito às normas da Lei se as descumprir.", estilo_justificado))
    elementos.append(Spacer(1, 0.2 * cm))

    elementos.append(Paragraph(
        "Nos termos do disposto no art. 5º da Resolução n. 5, de 10-11-2017, do Conselho Nacional de Política Criminal e Penitenciária do Ministério da Justiça e Cidadania, aceito a afixação, ao meu corpo, de dispositivo de monitoração eletrônica, sendo devidamente instalados a tornozeleira nº___________________, cinta, travas e me entregue o carregador, todos em perfeito funcionamento.", estilo_justificado))
    elementos.append(Spacer(1, 1 * cm))
    # Data e local
    data_atual = timezone.now().strftime('%d de %B de %Y')
    elementos.append(Paragraph(f"Maravilha, {data_atual}.", estilo_centralizado))
    elementos.append(Spacer(1, 1.5 * cm))

    # Assinatura
    elementos.append(Paragraph("_______________________________________", estilo_centralizado))
    elementos.append(Paragraph(f"{detento.nome}", estilo_centralizado))
    

    doc.build(elementos, onFirstPage=cabecalho_e_rodape_ume, onLaterPages=cabecalho_e_rodape_ume)

    buffer.seek(0)
    nome_arquivo = f"termo_monitorado_{detento.nome}.pdf"
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{nome_arquivo}"'
    return response

@checked_debug_decorador
def gerar_memorandos_todos(request):
    """
    Gera memorandos de todos os detentos em um único PDF.
    - Mês ímpar (jan, mar, mai...): Memorando Penal (modelo Memorando_Penal.py)
      → Metade superior: memorando genérico (com setores), metade inferior: PENAL
    - Mês par (fev, abr, jun...): Memorando SPenal (modelo Memorando_SPenal.py)
      → Dois memorandos genéricos (com setores), um para cada detento (2 por página)
    
    Ordem: Fechado primeiro, depois Semiaberto. Dentro de cada, por local_residencia e nome.
    """

    mes_atual = datetime.datetime.now().month
    mes_referencia, mes_corrente = _get_mes_referencia()
    
    # Buscar detentos ordenados: Fechado (F) primeiro, depois Semiaberto (SA)
    detentos = list(
        Relacao.objects
        .filter(local_galeria__in=['A', 'B', 'C', 'D', 'E'])
        .only('IPEN', 'nome', 'local_alocacao', 'local_residencia', 'local_galeria')
        .order_by('local_galeria', 'local_residencia', 'nome')
    )
    if not detentos:
        return HttpResponse(
            "Erro: Nenhum detento encontrado nas galerias A, B, C, D ou E.",
            content_type='text/plain',
            status=400
    )


    buffer = io.BytesIO()
    page_size = A4  # 595.28 x 841.89
    c = canvas.Canvas(buffer, pagesize=page_size)
    c.setTitle("Memorandos de Apenados")

    caminho_logo = os.path.join(settings.BASE_DIR, 'staticfiles', 'img', 'logo3.png')
    logo_existe = os.path.exists(caminho_logo)

    if mes_atual % 2 == 1:
        # ==========================================
        # MÊS ÍMPAR — Modelo Memorando_Penal.py
        # 1 detento por página
        # Superior: memorando genérico (com setores)
        # Inferior: memorando PENAL
        # ==========================================
        for i, detento in enumerate(detentos):
            nome_interno = _encurtar_nome(detento.nome)
            numero_ipen = str(detento.IPEN)

            c.setStrokeColorRGB(0, 0, 0, 0.7)
            c.setLineWidth(0.5)
            c.setFillColor("black")

            # ---- PRIMEIRO MEMORANDO (metade superior) ----
            # Cabeçalho
            c.setFont("Helvetica-Oblique", 11, leading=1)
            c.rotate(90)
            if logo_existe:
                c.drawImage(caminho_logo, 15 * cm, -3 * cm, width=2 * cm, height=2 * cm, mask='auto')
            c.drawString(17.5 * cm, -1.5 * cm, "ESTADO DE SANTA CATARINA")
            c.setFont("Helvetica-Oblique", 8, leading=1)
            c.drawString(17.5 * cm, -1.9 * cm, "SECRETARIA DE ESTADO DE JUSTIÇA E REINTEGRAÇÃO SOCIAL")
            c.drawString(17.5 * cm, -2.3 * cm, "PRESÍDIO REGIONAL DE MARAVILHA")
            c.rotate(270)

            # Componente ESCRITA (linhas para escrever)
            for j in range(12):
                c.rect((7 + j) * cm, 15 * cm, 1 * cm, 14.3 * cm, fill=0)

            # Componente assinatura e data
            c.rect(19.5 * cm, 15 * cm, 1 * cm, 14.3 * cm, fill=0)
            c.rect(19.5 * cm, 15 * cm, 1 * cm, 3 * cm, fill=0)
            c.rotate(90)
            c.setFont("Helvetica-Oblique", 8, leading=1)
            c.drawString(15 * cm, -19.3 * cm, "APENADO")
            c.drawCentredString(15.5 * cm, -19.8 * cm, "DATA")
            c.drawCentredString(19 * cm, -19.8 * cm, "ASSINATURA")
            c.rotate(270)

            # Componente Nome e Matrícula
            c.rect(4.8 * cm, 15 * cm, 1 * cm, 14.3 * cm, fill=0)
            c.rect(3.5 * cm, 15 * cm, 1 * cm, 11 * cm, fill=0)
            c.rect(3.5 * cm, 26 * cm, 1 * cm, 3.3 * cm)
            c.rect(2.5 * cm, 26 * cm, 1 * cm, 3.3 * cm, fill=0)
            c.setFont("Helvetica-Oblique", 8, leading=1)
            c.rotate(90)
            c.drawString(15.5 * cm, -3.8 * cm, "NOME")
            c.drawString(26.2 * cm, -3.8 * cm, "MATRÍCULA")
            c.setFont("Helvetica-Oblique", 14, leading=1)
            c.drawCentredString(20 * cm, -4.3 * cm, f"{nome_interno}")
            c.drawRightString(28.5 * cm, -4.3 * cm, f"{numero_ipen}")
            c.drawCentredString(27.5 * cm, -3.3 * cm, f"{mes_corrente}")
            c.setFont("Helvetica-Oblique", 12, leading=1)
            c.drawRightString(25.8 * cm, -3.3 * cm, "MEMORANDO DE APENADO")
            c.rotate(270)

            # Componente AO SETOR
            c.rect(4.8 * cm, 15 * cm, 2 * cm, 14.3 * cm, fill=0)
            c.setFont("Helvetica-Oblique", 8, leading=1)
            c.rotate(90)
            c.drawString(15.8 * cm, -5.2 * cm, "AO SETOR")
            c.setFont("Helvetica-Oblique", 12, leading=1)
            c.drawString(15.8 * cm, -5.6 * cm, "(  )PSICÓLOGA; (  )DIRETOR; (  )PECÚLIO; (  )EDUCAÇÃO;")
            c.drawString(15.7 * cm, -6.6 * cm, "(  )SOCIAL; (  )CHEFE DE SEGURANÇA e (  )OUTROS:__________")
            c.rotate(270)

            # ---- SEGUNDO MEMORANDO (metade inferior) — PENAL ----
            # Cabeçalho
            c.setFont("Helvetica-Oblique", 11, leading=1)
            c.rotate(90)
            if logo_existe:
                c.drawImage(caminho_logo, 0.2 * cm, -3 * cm, width=2 * cm, height=2 * cm, mask='auto')
            c.drawString(2.5 * cm, -1.5 * cm, "ESTADO DE SANTA CATARINA")
            c.setFont("Helvetica-Oblique", 8, leading=1)
            c.drawString(2.5 * cm, -1.9 * cm, "SECRETARIA DE ESTADO DE JUSTIÇA E REINTEGRAÇÃO SOCIAL")
            c.drawString(2.5 * cm, -2.3 * cm, "PRESÍDIO REGIONAL DE MARAVILHA")
            c.rotate(270)

            # Componente Nome e Matrícula
            c.rect(3.5 * cm, 0.2 * cm, 1 * cm, 14.3 * cm, fill=0)
            c.rect(3.5 * cm, 0.2 * cm, 1 * cm, 11 * cm, fill=0)
            c.rect(2.5 * cm, 11.2 * cm, 1 * cm, 3.3 * cm, fill=0)
            c.setFont("Helvetica-Oblique", 8, leading=1)
            c.rotate(90)
            c.drawString(0.8 * cm, -3.8 * cm, "NOME")
            c.drawString(11.5 * cm, -3.8 * cm, "MATRÍCULA")
            c.setFont("Helvetica-Oblique", 14, leading=1)
            c.drawCentredString(6 * cm, -4.3 * cm, f"{nome_interno}")
            c.drawRightString(14.3 * cm, -4.3 * cm, f"{numero_ipen}")
            c.drawCentredString(12.8 * cm, -3.3 * cm, f"{mes_referencia}")
            c.setFont("Helvetica-Oblique", 12, leading=1)
            c.drawRightString(11 * cm, -3.3 * cm, "MEMORANDO DE APENADO")
            c.rotate(270)

            # Componente AO SETOR — PENAL
            c.rect(4.8 * cm, 0.2 * cm, 1 * cm, 14.3 * cm, fill=0)
            c.setFont("Helvetica-Oblique", 8, leading=1)
            c.rotate(90)
            c.drawString(0.8 * cm, -5.2 * cm, "AO SETOR")
            c.setFont("Helvetica-Oblique", 14.3, leading=1)
            c.drawCentredString(7 * cm, -5.5 * cm, "PENAL")
            c.rotate(270)

            # Componente ESCRITA — PENAL
            for j in range(13):
                c.rect((6 + j) * cm, 0.2 * cm, 1 * cm, 14.3 * cm, fill=0)

            # Componente data e assinatura — PENAL
            c.rect(19.5 * cm, 0.2 * cm, 1 * cm, 14.3 * cm, fill=0)
            c.rect(19.5 * cm, 0.2 * cm, 1 * cm, 3 * cm, fill=0)
            c.rotate(90)
            c.setFont("Helvetica-Oblique", 8, leading=1)
            c.drawString(0.2 * cm, -19.3 * cm, "APENADO")
            c.drawCentredString(0.8 * cm, -19.8 * cm, "DATA")
            c.drawCentredString(4.2 * cm, -19.8 * cm, "ASSINATURA")
            c.rotate(270)

            c.showPage()

    else:
        # ==========================================
        # MÊS PAR — Modelo Memorando_SPenal.py
        # 2 detentos por página (superior e inferior)
        # Ambos memorandos genéricos (com setores)
        # ==========================================
        for i in range(0, len(detentos), 2):
            detento1 = detentos[i]
            nome_interno1 = _encurtar_nome(detento1.nome)
            numero_ipen1 = str(detento1.IPEN)

            # Verificar se existe segundo detento
            if i + 1 < len(detentos):
                detento2 = detentos[i + 1]
                nome_interno2 = _encurtar_nome(detento2.nome)
                numero_ipen2 = str(detento2.IPEN)
            else:
                nome_interno2 = ""
                numero_ipen2 = ""

            c.setStrokeColorRGB(0, 0, 0, 0.7)
            c.setLineWidth(0.5)
            c.setFillColor("black")

            # ---- PRIMEIRO MEMORANDO (metade superior) — Detento 1 ----
            # Cabeçalho
            c.setFont("Helvetica-Oblique", 11, leading=1)
            c.rotate(90)
            if logo_existe:
                c.drawImage(caminho_logo, 15 * cm, -3 * cm, width=2 * cm, height=2 * cm, mask='auto')
            c.drawString(17.5 * cm, -1.5 * cm, "ESTADO DE SANTA CATARINA")
            c.setFont("Helvetica-Oblique", 8, leading=1)
            c.drawString(17.5 * cm, -1.9 * cm, "SECRETARIA DE ESTADO DE JUSTIÇA E REINTEGRAÇÃO SOCIAL")
            c.drawString(17.5 * cm, -2.3 * cm, "PRESÍDIO REGIONAL DE MARAVILHA")
            c.rotate(270)

            # Componente ESCRITA
            for j in range(12):
                c.rect((7 + j) * cm, 15 * cm, 1 * cm, 14.3 * cm, fill=0)

            # Componente assinatura e data
            c.rect(19.5 * cm, 15 * cm, 1 * cm, 14.3 * cm, fill=0)
            c.rect(19.5 * cm, 15 * cm, 1 * cm, 3 * cm, fill=0)
            c.rotate(90)
            c.setFont("Helvetica-Oblique", 8, leading=1)
            c.drawString(15 * cm, -19.3 * cm, "APENADO")
            c.drawCentredString(15.5 * cm, -19.8 * cm, "DATA")
            c.drawCentredString(19 * cm, -19.8 * cm, "ASSINATURA")
            c.rotate(270)

            # Componente Nome e Matrícula — Detento 1
            c.rect(4.8 * cm, 15 * cm, 1 * cm, 14.3 * cm, fill=0)
            c.rect(3.5 * cm, 15 * cm, 1 * cm, 11 * cm, fill=0)
            c.rect(3.5 * cm, 26 * cm, 1 * cm, 3.3 * cm)
            c.rect(2.5 * cm, 26 * cm, 1 * cm, 3.3 * cm, fill=0)
            c.setFont("Helvetica-Oblique", 8, leading=1)
            c.rotate(90)
            c.drawString(15.5 * cm, -3.8 * cm, "NOME")
            c.drawString(26.2 * cm, -3.8 * cm, "MATRÍCULA")
            c.setFont("Helvetica-Oblique", 14, leading=1)
            c.drawCentredString(20.3 * cm, -4.3 * cm, f"{nome_interno1}")
            c.drawRightString(28.5 * cm, -4.3 * cm, f"{numero_ipen1}")
            c.drawCentredString(27.5 * cm, -3.3 * cm, f"{mes_corrente}")
            c.setFont("Helvetica-Oblique", 12, leading=1)
            c.drawRightString(25.8 * cm, -3.3 * cm, "MEMORANDO DE APENADO")
            c.rotate(270)

            # Componente AO SETOR — Detento 1
            c.rect(4.8 * cm, 15 * cm, 2 * cm, 14.3 * cm, fill=0)
            c.setFont("Helvetica-Oblique", 8, leading=1)
            c.rotate(90)
            c.drawString(15.8 * cm, -5.2 * cm, "AO SETOR")
            c.setFont("Helvetica-Oblique", 12, leading=1)
            c.drawString(15.8 * cm, -5.6 * cm, "(  )PSICÓLOGA; (  )DIRETOR; (  )PECÚLIO; (  )EDUCAÇÃO;")
            c.drawString(15.7 * cm, -6.6 * cm, "(  )SOCIAL; (  )CHEFE DE SEGURANÇA e (  )OUTROS:__________")
            c.rotate(270)

            # ---- SEGUNDO MEMORANDO (metade inferior) — Detento 2 ----
            # Cabeçalho
            c.setFont("Helvetica-Oblique", 11, leading=1)
            c.rotate(90)
            if logo_existe:
                c.drawImage(caminho_logo, 0.2 * cm, -3 * cm, width=2 * cm, height=2 * cm, mask='auto')
            c.drawString(2.5 * cm, -1.5 * cm, "ESTADO DE SANTA CATARINA")
            c.setFont("Helvetica-Oblique", 8, leading=1)
            c.drawString(2.5 * cm, -1.9 * cm, "SECRETARIA DE ESTADO DE JUSTIÇA E REINTEGRAÇÃO SOCIAL")
            c.drawString(2.5 * cm, -2.3 * cm, "PRESÍDIO REGIONAL DE MARAVILHA")
            c.rotate(270)

            # Componente Nome e Matrícula — Detento 2
            c.rect(3.5 * cm, 0.2 * cm, 1 * cm, 14.3 * cm, fill=0)
            c.rect(3.5 * cm, 0.2 * cm, 1 * cm, 11 * cm, fill=0)
            c.rect(2.5 * cm, 11.2 * cm, 1 * cm, 3.3 * cm, fill=0)
            c.setFont("Helvetica-Oblique", 8, leading=1)
            c.rotate(90)
            c.drawString(0.8 * cm, -3.8 * cm, "NOME")
            c.drawString(11.5 * cm, -3.8 * cm, "MATRÍCULA")
            c.setFont("Helvetica-Oblique", 14, leading=1)
            c.drawCentredString(6 * cm, -4.3 * cm, f"{nome_interno2}")
            c.drawRightString(14.3 * cm, -4.3 * cm, f"{numero_ipen2}")
            c.drawCentredString(12.8 * cm, -3.3 * cm, f"{mes_corrente}")
            c.setFont("Helvetica-Oblique", 12, leading=1)
            c.drawRightString(11 * cm, -3.3 * cm, "MEMORANDO DE APENADO")
            c.rotate(270)

            # Componente AO SETOR — Detento 2 (com setores)
            c.rect(4.8 * cm, 0.2 * cm, 1 * cm, 14.3 * cm, fill=0)
            c.rect(5.8 * cm, 0.2 * cm, 1 * cm, 14.3 * cm, fill=0)
            c.setFont("Helvetica-Oblique", 8, leading=1)
            c.rotate(90)
            c.drawString(0.8 * cm, -5.2 * cm, "AO SETOR")
            c.setFont("Helvetica-Oblique", 12, leading=1)
            c.drawCentredString(7 * cm, -5.6 * cm, "(  )PSICÓLOGA; (  )DIRETOR; (  )PECÚLIO; (  )EDUCAÇÃO;")
            c.drawString(0.3 * cm, -6.6 * cm, "(  )SOCIAL; (  )CHEFE DE SEGURANÇA e (  )OUTROS:__________")
            c.rotate(270)

            # Componente ESCRITA — Detento 2
            for j in range(12):
                c.rect((7 + j) * cm, 0.2 * cm, 1 * cm, 14.3 * cm, fill=0)

            # Componente data e assinatura — Detento 2
            c.rect(19.5 * cm, 0.2 * cm, 1 * cm, 14.3 * cm, fill=0)
            c.rect(19.5 * cm, 0.2 * cm, 1 * cm, 3 * cm, fill=0)
            c.rotate(90)
            c.setFont("Helvetica-Oblique", 8, leading=1)
            c.drawString(0.2 * cm, -19.3 * cm, "APENADO")
            c.drawCentredString(0.8 * cm, -19.8 * cm, "DATA")
            c.drawCentredString(4.2 * cm, -19.8 * cm, "ASSINATURA")
            c.rotate(270)

            c.showPage()

    c.save()

    buffer.seek(0)
    tipo_memo = "com_penal" if mes_atual % 2 == 1 else "sem_penal"
    nome_arquivo = f'memorandos_{tipo_memo}_{mes_corrente}_{datetime.date.today()}.pdf'
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{nome_arquivo}"'
    return response


@checked_debug_decorador
@csrf_exempt
def calculo_alimentacao(request):
    resultado = None
    registro = None
    historico = CalculoAlimentacao.objects.all()[:10]

    # Contagens automáticas do banco (para pré-preencher o formulário)
    contagens = Relacao.objects.aggregate(
        trabalho_externo_auto=Count('id', filter=Q(situacao_penal='TRABALHO EXTERNO')),
        saida_temporaria_auto=Count('id', filter=Q(situacao_penal='SAÍDA TEMPORÁRIA')),
        internos_fechado_auto=Count('id', filter=Q(local_galeria__in=['A', 'C'])),
        internos_semiaberto_auto=Count('id', filter=Q(local_galeria__in=['B', 'D'])),
        internos_pensao_auto=Count('id', filter=Q(local_galeria='E')),
    )

    trabalho_externo_auto = contagens['trabalho_externo_auto']
    saida_temporaria_auto = contagens['saida_temporaria_auto']
    internos_fechado_auto = contagens['internos_fechado_auto']
    internos_semiaberto_auto = contagens['internos_semiaberto_auto']
    internos_pensao_auto = contagens['internos_pensao_auto']
    #print("Contagens automáticas - Fechado:", internos_fechado_auto, "Semiaberto:", internos_semiaberto_auto, "Pensão:", internos_pensao_auto)

    if request.GET.get('almoco_plantao') is not None and request.GET.get('almoco_plantao') != '':
        almoco_plantao = int(request.GET.get('almoco_plantao', 0) or 0)
        lanche_plantao = int(request.GET.get('lanche_plantao', 0) or 0)
        janta_plantao = int(request.GET.get('janta_plantao', 0) or 0)
        almoco_administrativo = int(request.GET.get('almoco_administrativo', 0) or 0)
        lanche_administrativo = int(request.GET.get('lanche_administrativo', 0) or 0)
        quantidade_internos_fechado = int(request.GET.get('quantidade_internos_fechado', 0) or 0)
        quantidade_internos_semiaberto = int(request.GET.get('quantidade_internos_semiaberto', 0) or 0)
        quantidade_internos_custodia = int(request.GET.get('quantidade_internos_custodia', 0) or 0)
        quantidade_internos_pensao = int(request.GET.get('quantidade_internos_pensao', 0) or 0)
        quantidade_internos_saida_temporaria = int(request.GET.get('quantidade_internos_saida_temporaria', 0) or 0)
        trabalho_externo = int(request.GET.get('trabalho_externo', 0) or 0)
        outras_subtracoes = int(request.GET.get('outras_subtracoes', 0) or 0)
        observacoes = request.GET.get('observacoes', '-') or '-'

        registro = CalculoAlimentacao.objects.create(
            almoco_plantao=almoco_plantao,
            janta_plantao=janta_plantao,
            lanche_plantao=lanche_plantao,
            almoco_administrativo=almoco_administrativo,
            lanche_administrativo=lanche_administrativo,
            quantidade_internos_fechado=quantidade_internos_fechado,
            quantidade_internos_semiaberto=quantidade_internos_semiaberto,
            quantidade_internos_custodia=quantidade_internos_custodia,
            quantidade_internos_pensao=quantidade_internos_pensao,
            quantidade_internos_saida_temporaria=quantidade_internos_saida_temporaria,
            trabalho_externo=trabalho_externo,
            outras_subtracoes=outras_subtracoes,
            observacoes=observacoes,
        )

        historico = CalculoAlimentacao.objects.all()[:10]

    else:
        try:
            registro_ultimo = CalculoAlimentacao.objects.latest()
            almoco_plantao = registro_ultimo.almoco_plantao
            lanche_plantao = registro_ultimo.lanche_plantao
            janta_plantao = registro_ultimo.janta_plantao
            almoco_administrativo = registro_ultimo.almoco_administrativo
            lanche_administrativo = registro_ultimo.lanche_administrativo
            quantidade_internos_fechado = registro_ultimo.quantidade_internos_fechado
            quantidade_internos_semiaberto = registro_ultimo.quantidade_internos_semiaberto
            quantidade_internos_custodia = registro_ultimo.quantidade_internos_custodia
            quantidade_internos_pensao = registro_ultimo.quantidade_internos_pensao
            quantidade_internos_saida_temporaria = registro_ultimo.quantidade_internos_saida_temporaria
            trabalho_externo = registro_ultimo.trabalho_externo
            outras_subtracoes = registro_ultimo.outras_subtracoes
            observacoes = registro_ultimo.observacoes
            registro = registro_ultimo
        except CalculoAlimentacao.DoesNotExist:
            registro = None

    if registro is not None:
        # ...existing code... (cálculos)
        total_bruto_internos = (
            quantidade_internos_fechado 
            + quantidade_internos_semiaberto 
            + quantidade_internos_custodia 
            + quantidade_internos_pensao
        )
        total_subtracoes = (
            quantidade_internos_saida_temporaria 
            + trabalho_externo 
            + outras_subtracoes
        )

        almoco_internos = total_bruto_internos - total_subtracoes

        almoco_fechado = quantidade_internos_fechado + quantidade_internos_custodia
        almoco_semiaberto = quantidade_internos_semiaberto + quantidade_internos_pensao
        almoco_fechado_liquido = almoco_fechado
        almoco_semiaberto_liquido = almoco_semiaberto - total_subtracoes
        if almoco_semiaberto_liquido < 0:
            almoco_fechado_liquido = almoco_fechado + almoco_semiaberto_liquido
            almoco_semiaberto_liquido = 0

        janta_internos = total_bruto_internos - quantidade_internos_saida_temporaria

        janta_fechado = quantidade_internos_fechado + quantidade_internos_custodia
        janta_semiaberto = quantidade_internos_semiaberto + quantidade_internos_pensao
        janta_fechado_liquido = janta_fechado 
        janta_semiaberto_liquido = janta_semiaberto - quantidade_internos_saida_temporaria
        if janta_fechado_liquido < 0:
            janta_semiaberto_liquido = janta_semiaberto + janta_fechado_liquido
            janta_fechado_liquido = 0

        
        lanche_servidores = lanche_plantao + lanche_administrativo
    
        

        resultado = {
            'almoco_plantao': almoco_plantao,
            'lanche_plantao': lanche_plantao,
            'janta_plantao': janta_plantao,
            'almoco_administrativo': almoco_administrativo,
            'lanche_administrativo': lanche_administrativo ,
            'almoco_internos': almoco_internos,
            'janta_internos': janta_internos,
            'total_bruto_internos': total_bruto_internos,
            'total_subtracoes': total_subtracoes,
            'almoco_fechado': almoco_fechado,
            'almoco_semiaberto': almoco_semiaberto,
            'almoco_fechado_liquido': almoco_fechado_liquido,
            'almoco_semiaberto_liquido': almoco_semiaberto_liquido,
            'janta_fechado': janta_fechado,
            'janta_semiaberto': janta_semiaberto,
            'janta_fechado_liquido': janta_fechado_liquido,
            'janta_semiaberto_liquido': janta_semiaberto_liquido,
            'quantidade_internos_fechado': quantidade_internos_fechado,
            'quantidade_internos_semiaberto': quantidade_internos_semiaberto,
            'quantidade_internos_custodia': quantidade_internos_custodia,
            'quantidade_internos_pensao': quantidade_internos_pensao,
            'quantidade_internos_saida_temporaria': quantidade_internos_saida_temporaria,
            'trabalho_externo': trabalho_externo,
            'outras_subtracoes': outras_subtracoes,
            'observacoes': observacoes,
            'atualizado_em': timezone.localtime(registro.atualizado_em).strftime('%d/%m/%Y %H:%M'),
        }

    context = {
        'titulo': 'Cálculo de Alimentação',
        'descricao': 'Ferramenta para calcular a quantidade de refeições necessárias para a unidade prisional.',
        'resultado': resultado,
        'historico': historico,
        'ano_corrente': ANO_CORRENTE,
        'trabalho_externo_auto': trabalho_externo_auto,
        'saida_temporaria_auto': saida_temporaria_auto,
        'internos_fechado_auto':internos_fechado_auto,
        'internos_semiaberto_auto':internos_semiaberto_auto,
        'internos_pensao_auto':internos_pensao_auto,
    }

    return render(request, 'calculo_alimentacao.html', context)