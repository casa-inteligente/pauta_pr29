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

import pandas as pd
import json
import datetime
import locale
import io 
import os

from django.urls import reverse
from django.http import HttpResponseRedirect
from django.templatetags.static import static
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, FileResponse, HttpResponse
from django.core.files.storage import FileSystemStorage
from .forms.geradores import DescricaoKitHigieneForm, TermoRoupariaForm 

from django.db.models import Case, When, Value
from django.db.models.functions import Concat
from django.utils import timezone

from .process_table import process_pdf, process_regime_pdf, exctrai_date_exit
from .models import Relacao, DescricaoKitHigiene, Descricao_termo_rouparia

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

# @login_required
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


    #visualização para o chefe de segurança dos internos trabalhandos



# '''
#     Processa o relatorio 1.9 e atualiza o banco de dados
# '''


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
        fs = FileSystemStorage()
        filename = fs.save(pdf_file.name, pdf_file)
        file_path = fs.path(filename)

        process_pdf(file_path)

        return redirect('relação_detentos:relacao_list')
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
        fs = FileSystemStorage()
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
        'form': form,
        'ano_corrente': ANO_CORRENTE,
    })

def gerar_termo_rouparia(request, detento_id:int, numero_kit:int, regime:str, com_higiene:str):
    '''
    Gera e baixa um documento no formato PDF do termo de rouparia do detento
    Returns:
        FileResponse: Documento pdf para download
    
    Args:
        Request: ID do detento, numero do kit, regime (fechado ou semiaberto) e se inclui kit higiene    
    
    
    '''
    detento = get_object_or_404(Relacao, id=detento_id)
    #print(f'regime: {regime}')
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

    texto = f" 01) Os internos devem assinar a opção com um X;<br/>02) Na opção “observação” descrever o que está sendo entregue (tamanho e quantidade de uniforme);<br/>03) O termo de recebimento, devidamente assinado, deverá ser digitalizado e arquivado no IPEN do interno."
    elementos.append(Paragraph(texto, estilo_justificado))
        
    # Tabela 2x8 com estilo_justificado
    # Tabela com estrutura específica
    tabela_dados = []
    data_atual = timezone.now().strftime('%d/%m/%Y')

    # Linha 1: Duas colunas - INTERNO
    tabela_dados.append([
        Paragraph("INTERNO:", estilo_justificado),
        Paragraph(f"{detento.nome}", estilo_subtitulo),
        "",  # Célula vazia
        ""   # Célula vazia
    ])

    # Linha 2: Quatro colunas - IPEN e DATA
    tabela_dados.append([
        Paragraph("IPEN:", estilo_justificado),
        Paragraph(f"{detento.IPEN}", estilo_subtitulo),
        Paragraph(f"DATA: {data_atual}", estilo_justificado),
        ""
    ])

    # Linha 3: Duas colunas - X e Kit higiene
    if incluir_higiene:
        tabela_dados.append([
            Paragraph("X", estilo_centralizado),
            Paragraph("Kit higiene", estilo_justificado),
            "",  # Célula vazia
            ""   # Célula vazia
        ])
    else:
        tabela_dados.append([
            "",
            Paragraph("Kit higiene", estilo_justificado),
            "",  # Célula vazia
            ""   # Célula vazia
        ])

    # Adicione mais linhas conforme necessário (continuando a estrutura anterior)
    # Linha 4: Uniforme
    tabela_dados.append([
        Paragraph("X", estilo_centralizado),
        Paragraph("Uniforme", estilo_justificado),
        "",  # Célula vazia
        ""   # Célula vazia
    ])

    # Linha 5: Cobertor
    tabela_dados.append([
        Paragraph("X", estilo_centralizado),
        Paragraph("Cobertor", estilo_justificado),
        "",  # Célula vazia
        ""   # Célula vazia
    ])

    # Linha 6: Observação sobre uniforme
    tabela_dados.append([
        Paragraph("Observação:", estilo_subtitulo),
        "",
        "",  # Célula vazia
        ""   # Célula vazia
    ])

    tabela_dados.append([
        Paragraph("Se uniforme, quantidade e tamanho.", estilo_justificado),
        "",
        "",  # Célula vazia
        ""   # Célula vazia
    ])

    # Linha 7: Descrição do kit
    if incluir_higiene:
        tabela_dados.append([
        Paragraph(f"{descricao_rouparia}<br/> <br/>{descricao_kit_higiene}", estilo_justificado),
        "",
        "",  # Célula vazia
        ""   # Célula vazia
    ])
    else:
        tabela_dados.append([
            Paragraph(f"{descricao_rouparia}", estilo_justificado),
            "",
            "",  # Célula vazia
            ""   # Célula vazia
        ])

    tabela_dados.append([
        Paragraph(f"Kit número: {numero_kit}", estilo_justificado),
        "",
        "",  # Célula vazia
        ""   # Célula vazia
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
        ('SPAN', (1, 0), (3, 0)),  # Mesclar colunas 1-2 na linha 1
        # Mesclar células vazias para melhor aparência
        ('SPAN', (2, 1), (3, 1)),
        ('SPAN', (2, 0), (3, 0)),  # Mesclar colunas 3-4 na linha 1
        ('SPAN', (1, 2), (3, 2)),  # Mesclar colunas 3-4 na linha 3
        ('SPAN', (1, 3), (3, 3)),  # Mesclar colunas 3-4 na linha 4
        ('SPAN', (1, 4), (3, 4)),  # Mesclar colunas 3-4 na linha 5
        ('SPAN', (1, 5), (3, 5)),  # Mesclar colunas 3-4 na linha 6
        ('SPAN', (0, 6), (3, 6)),  # Mesclar colunas 3-4 na linha 7
        ('SPAN', (0, 7), (3, 7)),  # Mesclar colunas 3-4 na linha 8
        ('SPAN', (0, 8), (3, 8)),  # Mesclar colunas 3-4 na linha 9
    ]))

    elementos.append(tabela)
    elementos.append(Spacer(1, 1 * cm))
    
        
    # Data
    if checked_data:
        elementos.append(Paragraph(f"Recebido em {data_atual}", estilo_justificado))
        elementos.append(Spacer(1, 0.75 * cm))
    else:
        elementos.append(Paragraph(f"Recebido em _____/_______/_______", estilo_justificado))
        elementos.append(Spacer(1, 0.75 * cm))

    # Assinatura
    elementos.append(Paragraph("_______________________________________", estilo_justificado))
    elementos.append(Paragraph(f"{detento.nome}", estilo_justificado))
    elementos.append(Spacer(1, 0.75 * cm))  

    # Assinatura
    elementos.append(Paragraph("_______________________________________", estilo_justificado))
    elementos.append(Paragraph(f"Assinatura do servidor (nome completo)", estilo_justificado))
    elementos.append(Spacer(1, 0.75 * cm))
    
    # Gerar o PDF
    doc.build(elementos, onFirstPage=cabecalho_e_rodape, onLaterPages=cabecalho_e_rodape)

    buffer.seek(0)
    nome_arquivo = f'termo_rouparia_{detento.nome}_{numero_kit}.pdf'
    return FileResponse(buffer, as_attachment=True, filename=nome_arquivo)

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
        'empresas_conveniadas': Relacao.empresas_conveniadas
    })

def gerar_termo_kit_higiene(request):
    #print("Gerando termo kit higiene...")
    #detentos = Relacao.objects.all().order_by('local_alocacao', 'regime','nome')
    detentos = (
        Relacao.objects
        .only('IPEN', 'nome', 'local_alocacao', 'local_residencia')  # Busca apenas campos necessários
        .order_by('local_alocacao', 'local_residencia', 'nome')
    )
    

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
    checked_kit = DescricaoKitHigiene.objects.first().checked_kit_higiene

    elementos = []

    for i, detento in enumerate(detentos):
        # Espaço do cabeçalho
        elementos.append(Spacer(1, 1.5 * cm))
        
        # Título
        elementos.append(Paragraph("<b>TERMO DE RECEBIMENTO</b>", estilo_titulo))
        elementos.append(Spacer(1, 0.5 * cm))
        texto = "Instruções:"
        elementos.append(Paragraph(texto, estilo_subtitulo))

        texto = f" 01) Os internos devem assinar a opção com um X;<br/>02) Na opção “observação” descrever o que está sendo entregue (tamanho e quantidade de uniforme); <br/> 03) O termo de recebimento, devidamente assinado, deverá ser digitalizado e arquivado no IPEN do interno."
        elementos.append(Paragraph(texto, estilo_justificado))
        
        # Tabela 2x8 com estilo_justificado
        # Tabela com estrutura específica
        tabela_dados = []
        data_atual = timezone.now().strftime('%d/%m/%Y')

        # Linha 1: Duas colunas - INTERNO
        tabela_dados.append([
            Paragraph("INTERNO:", estilo_justificado),
            Paragraph(f"{detento.nome}", estilo_justificado),
            "",  # Célula vazia
            ""   # Célula vazia
        ])

        # Linha 2: Quatro colunas - IPEN e DATA
        tabela_dados.append([
            Paragraph("IPEN:", estilo_justificado),
            Paragraph(f"{detento.IPEN}", estilo_justificado),
            Paragraph(f"DATA: {data_atual}", estilo_justificado),
            ""
        ])

        # Linha 3: Duas colunas - X e Kit higiene
        if checked_kit:
            tabela_dados.append([
                Paragraph("X", estilo_centralizado),
                Paragraph("Kit higiene", estilo_justificado),
                "",  # Célula vazia
                ""   # Célula vazia
            ])
        else:
            tabela_dados.append([
                "",
                Paragraph("Kit higiene", estilo_justificado),
                "",  # Célula vazia
                ""   # Célula vazia
            ])

        # Adicione mais linhas conforme necessário (continuando a estrutura anterior)
        # Linha 4: Uniforme
        tabela_dados.append([
            Paragraph(" ", estilo_centralizado),
            Paragraph("Uniforme", estilo_justificado),
            "",  # Célula vazia
            ""   # Célula vazia
        ])

        # Linha 5: Cobertor
        tabela_dados.append([
            "",
            Paragraph("Cobertor", estilo_justificado),
            "",  # Célula vazia
            ""   # Célula vazia
        ])

        # Linha 6: Observação sobre uniforme
        tabela_dados.append([
            Paragraph("Observação:", estilo_subtitulo),
            "",
            "",  # Célula vazia
            ""   # Célula vazia
        ])

        tabela_dados.append([
            Paragraph("Se uniforme, quantidade e tamanho.", estilo_justificado),
            "",
            "",  # Célula vazia
            ""   # Célula vazia
        ])

        # Linha 7: Descrição do kit
        tabela_dados.append([
            Paragraph(f"{descricao_kit_higiene}", estilo_justificado),
            "",
            "",  # Célula vazia
            ""   # Célula vazia
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
            ('SPAN', (1, 0), (3, 0)),  # Mesclar colunas 1-2 na linha 1
            # Mesclar células vazias para melhor aparência
            ('SPAN', (2, 1), (3, 1)),
            ('SPAN', (2, 0), (3, 0)),  # Mesclar colunas 3-4 na linha 1
            ('SPAN', (1, 2), (3, 2)),  # Mesclar colunas 3-4 na linha 3
            ('SPAN', (1, 3), (3, 3)),  # Mesclar colunas 3-4 na linha 4
            ('SPAN', (1, 4), (3, 4)),  # Mesclar colunas 3-4 na linha 5
            ('SPAN', (1, 5), (3, 5)),  # Mesclar colunas 3-4 na linha 6
            ('SPAN', (0, 6), (3, 6)),  # Mesclar colunas 3-4 na linha 7
            ('SPAN', (0, 7), (3, 7)),  # Mesclar colunas 3-4 na linha 7
        ]))

        elementos.append(tabela)
        elementos.append(Spacer(1, 1 * cm))
        
        # Data
        if checked_data:
            elementos.append(Paragraph(f"Recebido em {data_atual}", estilo_justificado))
            elementos.append(Spacer(1, 0.75 * cm))
        else:
            elementos.append(Paragraph(f"Recebido em _____/_______/_______", estilo_justificado))
            elementos.append(Spacer(1, 0.75 * cm))

        # Assinatura
        elementos.append(Paragraph("_______________________________________", estilo_justificado))
        elementos.append(Paragraph(f"{detento.nome}", estilo_justificado))
        elementos.append(Spacer(1, 0.75 * cm))  

        # Assinatura
        elementos.append(Paragraph("_______________________________________", estilo_justificado))
        elementos.append(Paragraph(f"Assinatura do servidor (nome completo)", estilo_justificado))
        elementos.append(Spacer(1, 0.75 * cm))


        # Adiciona quebra de página se não for o último detento
        if i < len(detentos) - 1:
            elementos.append(PageBreak())  # Força nova página

    # Gerar o PDF com cabeçalho e rodapé
    doc.build(elementos, onFirstPage=cabecalho_e_rodape, onLaterPages=cabecalho_e_rodape)

    buffer.seek(0)
    response = FileResponse(
        buffer, 
        as_attachment=True, 
        filename=f'kit_higiene_{datetime.date.today()}.pdf'
    )
    return response

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
    return FileResponse(buffer, as_attachment=True, filename=nome_arquivo)

def cabecalho_e_rodape(canvas, doc):
    from reportlab.lib.utils import ImageReader
   

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
    from reportlab.lib.utils import ImageReader
   

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
    return FileResponse(buffer, as_attachment=True, filename=nome_arquivo)