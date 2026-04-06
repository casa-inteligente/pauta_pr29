# /media/ogliari/backup_ssd/projetos-da-cadeia/pauta_pr29/projeto_pauta/resenha_livro/views.py

# /media/ogliari/backup_ssd/projetos-da-cadeia/pauta_pr29/projeto_pauta/resenha_livro/views.py

import datetime
import os
import re
import shutil
from collections import OrderedDict
from io import BytesIO
from pathlib import Path

import pypdfium2 as pdfium
import pytesseract
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .forms import AlunoForm, PeriodoLeituraForm, ResenhaLivroForm
from .models import Aluno, PeriodoLeitura, ResenhaLivro, Turma


# Registre Arial e Arial-Bold (se quiser usar negrito)
# Registre Arial e Arial-Bold (se quiser usar negrito)
# Caminhos relativos à pasta base do projeto
arial_path = os.path.join(settings.BASE_DIR, 'projeto_pauta', 'static', 'fonts', 'arial.ttf')
arial_bold_path = os.path.join(settings.BASE_DIR, 'projeto_pauta', 'static', 'fonts', 'arialbd.ttf')

# Registra as fontes
pdfmetrics.registerFont(TTFont('Arial', arial_path))
pdfmetrics.registerFont(TTFont('Arial-Bold', arial_bold_path))


def listar_alunos(request):
    """Listar todos os alunos e suas resenhas por período de leitura."""
    try:
        periodos = PeriodoLeitura.objects.all().order_by('-data_resenha')
        if not periodos.exists():
            resenhas_por_periodo = {}
        else:
            resenhas_por_periodo = {
                periodo: ResenhaLivro.objects.filter(
                    periodoLeitura=periodo
                ).select_related(
                    'aluno',
                    'aluno__turma',
                    'periodoLeitura',
                )
                for periodo in periodos
            }
    except Exception:
        resenhas_por_periodo = {}

    return render(request, 'listar_alunos.html', {
        'resenhas_por_periodo': resenhas_por_periodo,
        'titulo': 'Listar Alunos',
        'ano_corrente': datetime.datetime.now().year,
    })


def imprimir_resenha(request, aluno_id, periodo_id):
    """Renderiza a página para imprimir a resenha do aluno."""
    aluno = get_object_or_404(Aluno.objects.using('resenha_livro'), id=aluno_id)
    periodo = get_object_or_404(PeriodoLeitura, id=periodo_id)
    resenhas = ResenhaLivro.objects.using('resenha_livro').filter(aluno=aluno, periodoLeitura=periodo)
    linhas = range(68)

    return render(request, 'imprimir_resenha.html', {
        'titulo': 'Imprimir Resenha',
        'aluno': aluno,
        'resenhas': resenhas,
        'linhas': linhas,
    })


def adicionar_resenha(request):
    """Adicionar uma nova resenha."""
    if request.method == 'POST':
        form = ResenhaLivroForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('resenha_livro:listar_alunos')
    else:
        form = ResenhaLivroForm()
    return render(request, 'adicionar_resenha.html', {
        'form': form,
        'titulo': 'Adicionar Resenha',
    })


def editar_resenha(request, resenha_id):
    """Editar uma resenha existente."""
    resenha = get_object_or_404(ResenhaLivro, id=resenha_id)
    if request.method == 'POST':
        form = ResenhaLivroForm(request.POST, instance=resenha)
        if form.is_valid():
            form.save()
            return redirect('resenha_livro:listar_alunos')
    else:
        form = ResenhaLivroForm(instance=resenha)
    return render(request, 'editar_resenha.html', {
        'form': form,
        'titulo': 'Editar Resenha',
        'ano_corrente': datetime.datetime.now().year,
    })


def excluir_resenha(request, resenha_id):
    """Excluir uma resenha existente."""
    resenha = get_object_or_404(ResenhaLivro, id=resenha_id)
    resenha.delete()
    return redirect('resenha_livro:listar_alunos')


def gerar_todas_resenhas(request, periodo_id, aluno_id=None):
    """Gerar PDF das resenhas de um período ou de um aluno específico dentro do período."""
    periodo = get_object_or_404(PeriodoLeitura, id=periodo_id)

    resenhas = (
        ResenhaLivro.objects
        .filter(periodoLeitura=periodo)
        .select_related('aluno', 'aluno__turma', 'periodoLeitura')
        .order_by('aluno__nome', 'id')
    )

    if aluno_id is not None:
        resenhas = resenhas.filter(aluno_id=aluno_id)

    resenhas = list(resenhas)

    if not resenhas:
        if aluno_id is not None:
            return HttpResponse(
                'Nenhuma resenha encontrada para este aluno neste período.',
                status=404
            )
        return HttpResponse(
            'Nenhuma resenha cadastrada para este período.',
            status=404
        )

    response = HttpResponse(content_type='application/pdf')

    if aluno_id is not None:
        nome_aluno = slugify(resenhas[0].aluno.nome) or f'aluno_{aluno_id}'
        response['Content-Disposition'] = (
            f'inline; filename="resenhas_{nome_aluno}_periodo_{periodo.id}.pdf"'
        )
    else:
        response['Content-Disposition'] = (
            f'inline; filename="resenhas_periodo_{periodo.id}.pdf"'
        )

    pdf = canvas.Canvas(response, pagesize=A4)
    pdf.setLineWidth(0.5)
    pdf.setStrokeColorRGB(0, 0, 0, 0.7)
    pdf.setAuthor("OGLTech")
    largura, altura = A4

    def finalizar_pagina():
        pdf.saveState()
        pdf.setFont("Arial", 8)
        pdf.setFillColorRGB(0, 0, 0, 0.5)
        pdf.drawCentredString(largura / 2, 20, "Emissão Automática")
        pdf.restoreState()
        pdf.showPage()

    def linha_pontilhada(x1, y1, x2, y2):
        pdf.saveState()
        pdf.setLineWidth(0.9)
        pdf.setStrokeColorRGB(1, 1, 1, 0.01)
        pdf.setDash(1, 2)
        pdf.line(x1, y1, x2, y2)
        pdf.restoreState()

    for resenha in resenhas:
        pdf.setFont("Arial-Bold", 16)
        pdf.setLineWidth(0.5)
        pdf.setStrokeColorRGB(0, 0, 0, 0.7)
        titulo = "PROJETO REMIÇÃO PELA LEITURA"
        pdf.drawCentredString(largura / 2, altura - 50, titulo)

        pdf.setFont("Arial", 12)
        y = altura - 100
        margem_esquerda = 50
        margem_direita = largura - 50

        linha_pontilhada(margem_esquerda, y + 20, margem_direita, y + 20)
        linha_pontilhada(margem_esquerda, y - 8, margem_direita, y - 8)
        linha_pontilhada(margem_esquerda, y - 25, margem_direita, y - 25)
        linha_pontilhada(margem_esquerda, y - 45, margem_direita, y - 45)
        linha_pontilhada(margem_esquerda, y - 65, margem_direita, y - 65)
        linha_pontilhada(margem_esquerda, y - 85, margem_direita, y - 85)

        linha_pontilhada(margem_esquerda + 280, y - 8, margem_esquerda + 280, y - 45)
        linha_pontilhada(margem_esquerda, y + 20, margem_esquerda, y - 85)
        linha_pontilhada(margem_direita, y + 20, margem_direita, y - 85)

        pdf.drawString(margem_esquerda + 10, y, f"Aluno: {resenha.aluno.nome}")
        y -= 20
        pdf.drawString(
            margem_esquerda + 10,
            y,
            f"Data da Resenha: {resenha.dataResenha.strftime('%d/%m/%Y')}"
        )
        pdf.drawString(
            margem_direita - 200,
            y,
            f"Período de Leitura: {resenha.periodoLeitura.intervalo_leitura}"
        )
        y -= 20
        pdf.drawString(
            margem_esquerda + 10,
            y,
            "Local: CEJA/Ud Presídio Regional de Maravilha"
        )
        pdf.drawString(
            margem_direita - 200,
            y,
            f"Professor(a): {resenha.nomeProfessor}"
        )

        y -= 20
        pdf.drawCentredString(margem_direita - 250, y, f"{resenha.nomelivro}")
        y -= 20
        pdf.drawString(margem_esquerda + 15, y, f"{resenha.nomeAutor}")

        size_lines = 18
        qtd_linha_1folha = 31
        y -= 40

        pdf.line(
            margem_esquerda,
            y,
            margem_esquerda,
            y - (size_lines * (qtd_linha_1folha - 1))
        )
        pdf.line(
            margem_direita,
            y,
            margem_direita,
            y - (size_lines * (qtd_linha_1folha - 1))
        )

        for _ in range(qtd_linha_1folha):
            pdf.line(margem_esquerda, y, margem_direita, y)
            y -= size_lines

            if y < 50:
                finalizar_pagina()
                pdf.setFont("Arial", 8)
                y = altura - 50

        finalizar_pagina()
        pdf.setFont("Arial", 8)
        y = altura - 50

        qtd_linha_2folha = 40
        pdf.line(
            margem_esquerda,
            y,
            margem_esquerda,
            y - (size_lines * (qtd_linha_2folha - 1))
        )
        pdf.line(
            margem_direita,
            y,
            margem_direita,
            y - (size_lines * (qtd_linha_2folha - 1))
        )

        for _ in range(qtd_linha_2folha):
            pdf.line(margem_esquerda, y, margem_direita, y)
            pdf.setLineWidth(0.5)
            pdf.setStrokeColorRGB(0, 0, 0, 0.7)

            y -= size_lines
            if y < 50:
                finalizar_pagina()
                pdf.setFont("Arial", 8)
                y = altura - 50

        finalizar_pagina()

    pdf.save()
    return response


def adicionar_aluno_popup(request):
    """Adicionar um novo aluno por modal HTMX."""
    if request.method == 'POST':
        form = AlunoForm(request.POST)
        if form.is_valid():
            form.save()
            response = HttpResponse('')
            response['HX-Trigger'] = 'alunoAdicionado'
            return response
    else:
        form = AlunoForm()

    return render(request, 'adicionar_aluno_popup.html', {
        'form': form,
        'titulo': 'Adicionar Aluno',
    })


@login_required
def gerar_decraracao_resenha(request, aluno_id):
    """Gerar declaração da resenha."""
    pass


@login_required
def configuracao_resenhas(request):
    """Tela de configurações das resenhas."""
    ano_atual = datetime.datetime.now().year

    context = {
        'titulo': 'Configurações de Resenhas',
        'ano_corrente': ano_atual,
        'total_alunos': Aluno.objects.filter(
            resenhas__periodoLeitura__data_resenha__year=ano_atual
        ).distinct().count(),
        'total_resenhas': ResenhaLivro.objects.filter(
            periodoLeitura__data_resenha__year=ano_atual
        ).count(),
        'total_periodos': PeriodoLeitura.objects.filter(
            data_resenha__year=ano_atual
        ).count(),
    }
    return render(request, 'configuracao_resenhas.html', context)

@login_required
def adicionar_periodo_leitura(request):
    """Adicionar um novo período de leitura."""
    if request.method == 'POST':
        form = PeriodoLeituraForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('resenha_livro:configuracao_resenhas')
    else:
        form = PeriodoLeituraForm()

    return render(request, 'adicionar_periodo_leitura.html', {
        'form': form,
        'titulo': 'Adicionar Período de Leitura',
        'ano_corrente': datetime.datetime.now().year,
    })


def _resolver_caminho_resenha_pdf(path_resenha):
    """Resolve o caminho do PDF da resenha."""
    if not path_resenha:
        return None

    caminho = Path(path_resenha)

    if caminho.is_absolute() and caminho.exists():
        return caminho

    caminho_media = Path(settings.MEDIA_ROOT) / path_resenha
    if caminho_media.exists():
        return caminho_media

    caminho_base = Path(settings.BASE_DIR) / path_resenha
    if caminho_base.exists():
        return caminho_base

    return None

def _gerar_declaracao_pdf_bytes(aluno, resenhas):
    """Gera uma declaração única por aluno, com cabeçalho, parágrafo e tabela."""
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=36,
        bottomMargin=36,
    )

    estilos = getSampleStyleSheet()

    estilo_instituicao = ParagraphStyle(
        name='Instituicao',
        parent=estilos['Normal'],
        fontName='Arial',
        fontSize=10,
        leading=10,
        alignment=TA_LEFT,
        textColor=colors.black,
        spaceAfter=0,
    )

    estilo_corpo = ParagraphStyle(
        name='CorpoDeclaracao',
        parent=estilos['Normal'],
        fontName='Arial',
        fontSize=10,
        leading=12,
        alignment=TA_JUSTIFY,
        textColor=colors.black,
    )

    estilo_titulo = ParagraphStyle(
        name='TituloDeclaracao',
        parent=estilos['Normal'],
        fontName='Arial-Bold',
        fontSize=12,
        leading=18,
        alignment=TA_CENTER,
        textColor=colors.black,
    )


    estilo_tabela = ParagraphStyle(
        name='TabelaTexto',
        parent=estilos['Normal'],
        fontName='Arial',
        fontSize=9,
        leading=11,
        alignment=TA_LEFT,
        textColor=colors.black,
    )

    estilo_tabela_cabecalho = ParagraphStyle(
        name='TabelaCabecalho',
        parent=estilos['Normal'],
        fontName='Arial-Bold',
        fontSize=9,
        leading=11,
        alignment=TA_LEFT,
        textColor=colors.white,
    )

    estilo_data = ParagraphStyle(
        name='DataLocal',
        parent=estilos['Normal'],
        fontName='Arial',
        fontSize=11,
        leading=14,
        alignment=TA_RIGHT,
        textColor=colors.black,
    )

    estilo_rodape = ParagraphStyle(
        name='RodapeSistema',
        parent=estilos['Normal'],
        fontName='Arial',
        fontSize=8,
        leading=10,
        alignment=TA_LEFT,
        textColor=colors.HexColor('#6b7280'),
    )

    estilo_quadro_final = ParagraphStyle(
        name='QuadroFinal',
        parent=estilos['Normal'],
        fontName='Arial',
        fontSize=9,
        leading=11,
        alignment=TA_CENTER,
        textColor=colors.black,
        spaceBefore=0,
        spaceAfter=0,
    )

    story = []

    logo_path = os.path.join(
        settings.BASE_DIR,
        'resenha_livro',
        'static',
        'resenha_livro',
        'img',
        'logo_ceja.png',
    )

    if os.path.exists(logo_path):
        logo = Image(logo_path, width=52, height=52)
    else:
        logo = Paragraph("Logo", estilo_tabela)

    nome_instituicao = Paragraph(
        "ESTADO DE SANTA CATARINA<br/>"
        "COORDENADORIA REGIONAL DE EDUCAÇÃO<br/>"
        "CENTRO DE EDUCAÇÃO DE JOVENS E ADULTOS – CEJA - MH<br/>"
        "Endereço: Rua: General Ozório - 319 – CEP: 89874-000<br/>"
        "Telefone: (49) 3664-6632<br/>"
        "E-mail: cejamaravilha@sed.sc.gov.br",
        estilo_instituicao
    )

    tabela_cabecalho = Table(
        [[logo, nome_instituicao]],
        colWidths=[65, doc.width - 65],
    )
    tabela_cabecalho.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))

    story.append(tabela_cabecalho)
    story.append(Spacer(1, 18))

    numero_obras = len(resenhas)
    numero_matricula = aluno.matricula or 'não informado'

    texto_titulo = Paragraph(
        (
            "DECLARAÇÃO DE PARTICIPAÇÃO NO PROJETO DESPERTAR PELA LEITURA"
        ), 
        estilo_titulo
    )

    story.append(texto_titulo)
    story.append(Spacer(1, 16))


    texto_declaracao = Paragraph(
        (
            f"Certificamos, para os devidos fins de Remição de Pena pela Leitura, que o aluno <font name='Arial-Bold'>{aluno.nome}</font>, regularmente matriculado no Centro de Educação de Jovens e Adultos de Maravilha – CEJA, sob o número de inscrição "
            f"<font name='Arial-Bold'>{numero_matricula}</font>, participou do Projeto "
            f"“Despertar pela Leitura”, realizado no Presídio Regional de Maravilha, "
            f"realizando a leitura de <font name='Arial-Bold'>{numero_obras}</font> obra(s), "
            f"na forma discriminada no quadro abaixo."
        ),
        estilo_corpo
    )

    story.append(texto_declaracao)
    story.append(Spacer(1, 16))

    dados_tabela = [[
        Paragraph("N.", estilo_tabela_cabecalho),
        Paragraph("Obra - Autor", estilo_tabela_cabecalho),
        Paragraph("Período", estilo_tabela_cabecalho),
        Paragraph("Resultado", estilo_tabela_cabecalho),
    ]]

    for indice, resenha in enumerate(resenhas, start=1):
        resultado = "Satisfatória" if resenha.aprovada else "Insatisfatória"

        obra_autor = Paragraph(
            f"{resenha.nomelivro} - {resenha.nomeAutor}",
            estilo_tabela
        )

        periodo = Paragraph(
            f"{resenha.periodoLeitura.intervalo_leitura}",
            estilo_tabela
        )

        dados_tabela.append([
            Paragraph(str(indice), estilo_tabela),
            obra_autor,
            periodo,
            Paragraph(resultado, estilo_tabela),
        ])

    tabela_resenhas = Table(
        dados_tabela,
        colWidths=[30, 305, 80, 80],
        repeatRows=1,
    )

    tabela_resenhas.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.black),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Arial-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))

    story.append(tabela_resenhas)
    story.append(Spacer(1, 18))

    hoje = datetime.datetime.now()
    dia = hoje.strftime('%d')
    mes = hoje.strftime('%B').capitalize()
    ano = hoje.strftime('%Y')

    story.append(
        Paragraph(
            f"Maravilha, {dia} de {mes} de {ano}",
            estilo_data
        )
    )


    # Caracteristicas da gestora do CEJA
    story.append(Spacer(1, 18))

    quadro_coluna_1 = Paragraph(
        (
            "CEJA – Centro de Educação de Jovens e Adultos<br/>"
            "Rua General Osório, 319, Ed. Iluminato, Sala 102<br/>"
            "Centro – Maravilha/SC – CEP: 89.874-000<br/>"
            "Telefone: (49) 3664 6632<br/>"
            "E-mail: cejamaravilha@sed.sc.gov.br<br/>"
            "Resolução n° 093 e no parecer n° 221,<br/>"
            "Aprovado em 02/09/2003."
        ),
        estilo_quadro_final
    )

    quadro_coluna_2 = Paragraph(
        (
            "JOICE HENDGES DA LUS<br/>"
            "Diretora de unidade<br/>"
            "Matrícula 334464-9-04<br/>"
            "CEJA MARAVILHA"
        ),
        estilo_quadro_final
    )

    tabela_final = Table(
        [[quadro_coluna_1, quadro_coluna_2]],
        colWidths=[doc.width / 2, doc.width / 2],
    )

    tabela_final.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.7, colors.HexColor('#4b5563'), None, (2, 3)),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#6b7280'), None, (1, 2)),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))

    story.append(tabela_final)

    def desenhar_rodape(canvas_obj, doc_obj):
        canvas_obj.saveState()
        canvas_obj.setFont('Arial', 8)
        canvas_obj.setFillColor(colors.HexColor('#6b7280'))
        canvas_obj.drawCentredString(
            A4[0] / 2,
            20,
            "Emissão automática - PR29"
        )
        canvas_obj.restoreState()

    doc.build(story, onFirstPage=desenhar_rodape, onLaterPages=desenhar_rodape)
    buffer.seek(0)
    return buffer


def _gerar_pagina_aviso_sem_pdf(resenha):
    """Cria uma página PDF avisando ausência do anexo da resenha."""
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    largura, altura = A4

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawCentredString(largura / 2, altura - 80, "AVISO DE ANEXO NÃO ENCONTRADO")

    texto = pdf.beginText(70, altura - 140)
    texto.setFont("Helvetica", 12)
    texto.setLeading(22)

    linhas = [
        f"Aluno(a): {resenha.aluno.nome}",
        f"Obra: {resenha.nomelivro}",
        f"Autor: {resenha.nomeAutor}",
        f"Período: {resenha.periodoLeitura.intervalo_leitura}",
        "",
        "Esta declaração foi gerada, porém o arquivo PDF da resenha",
        "não foi localizado no caminho informado.",
    ]

    if resenha.path_resenha:
        linhas.extend([
            "",
            f"Caminho informado: {resenha.path_resenha}",
        ])
    else:
        linhas.extend([
            "",
            "Nenhum caminho de anexo foi cadastrado para esta resenha.",
        ])

    for linha in linhas:
        texto.textLine(linha)

    pdf.drawText(texto)
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer

@login_required
def gerar_declaracao(request):
    """Lista todas as resenhas agrupadas por ano, turma e aluno."""
    resenhas = (
        ResenhaLivro.objects
        .select_related(
            'aluno',
            'aluno__turma',
            'periodoLeitura',
        )
        .order_by(
            '-periodoLeitura__data_resenha',
            'aluno__turma__nome',
            'aluno__nome',
            'nomelivro',
        )
    )

    dados_por_ano = {}

    for resenha in resenhas:
        ano = resenha.periodoLeitura.data_resenha.year
        turma_nome = resenha.aluno.turma.nome
        aluno_id = resenha.aluno.id

        if ano not in dados_por_ano:
            dados_por_ano[ano] = {}

        if turma_nome not in dados_por_ano[ano]:
            dados_por_ano[ano][turma_nome] = {}

        if aluno_id not in dados_por_ano[ano][turma_nome]:
            dados_por_ano[ano][turma_nome][aluno_id] = {
                'aluno': resenha.aluno,
                'resenhas': [],
            }

        dados_por_ano[ano][turma_nome][aluno_id]['resenhas'].append(resenha)

    anos_organizados = []
    for ano, turmas in dados_por_ano.items():
        turmas_lista = []
        for turma_nome, alunos_dict in turmas.items():
            turmas_lista.append({
                'nome': turma_nome,
                'alunos': list(alunos_dict.values()),
            })

        turmas_lista.sort(key=lambda item: item['nome'])
        anos_organizados.append({
            'ano': ano,
            'turmas': turmas_lista,
        })

    anos_organizados.sort(key=lambda item: item['ano'], reverse=True)

    context = {
        'titulo': 'Gerar Declaração',
        'ano_corrente': datetime.datetime.now().year,
        'anos_organizados': anos_organizados,
    }
    return render(request, 'gerar_declaracao.html', context)



@login_required
@require_POST
def alternar_gerado_declaracao(request, resenha_id):
    """Marca ou desmarca o status de geração da declaração."""
    resenha = get_object_or_404(ResenhaLivro, id=resenha_id)
    valor = request.POST.get('gerado_declaracao') == 'on'

    resenha.gerado_declaracao = valor
    #resenha.atualizado_por = request.user
    resenha.save(update_fields=['gerado_declaracao', 'atualizado_em'])

    return HttpResponse(status=204)


@login_required
@require_POST
def popup_confirmar_geracao_declaracao(request):
    """Exibe popup com as resenhas selecionadas para geração."""
    ids = request.POST.getlist('resenhas_ids')

    resenhas = (
        ResenhaLivro.objects
        .filter(id__in=ids)
        .select_related('aluno', 'aluno__turma', 'periodoLeitura')
        .order_by('aluno__turma__nome', 'aluno__nome', '-periodoLeitura__data_resenha')
    )

    context = {
        'resenhas': resenhas,
        'ids': [str(item.id) for item in resenhas],
    }
    return render(request, 'popup_confirmar_geracao_declaracao.html', context)


@login_required
@require_POST
def gerar_declaracoes_selecionadas(request):
    """Gera um PDF único com 1 declaração por aluno + anexos das resenhas em sequência."""
    ids = request.POST.getlist('resenhas_ids')

    resenhas = list(
        ResenhaLivro.objects
        .filter(id__in=ids)
        .select_related('aluno', 'aluno__turma', 'periodoLeitura')
        .order_by(
            'aluno__turma__nome',
            'aluno__nome',
            'periodoLeitura__data_resenha',
            'id',
        )
    )

    grupos_alunos = OrderedDict()
    for resenha in resenhas:
        if resenha.aluno_id not in grupos_alunos:
            grupos_alunos[resenha.aluno_id] = {
                'aluno': resenha.aluno,
                'resenhas': [],
            }
        grupos_alunos[resenha.aluno_id]['resenhas'].append(resenha)

    writer = PdfWriter()

    for grupo in grupos_alunos.values():
        aluno = grupo['aluno']
        resenhas_aluno = grupo['resenhas']

        declaracao_buffer = _gerar_declaracao_pdf_bytes(aluno, resenhas_aluno)
        declaracao_reader = PdfReader(declaracao_buffer)

        for page in declaracao_reader.pages:
            writer.add_page(page)

        for resenha in resenhas_aluno:
            caminho_pdf = _resolver_caminho_resenha_pdf(resenha.path_resenha)

            if caminho_pdf and caminho_pdf.suffix.lower() == '.pdf':
                with open(caminho_pdf, 'rb') as arquivo_pdf:
                    anexo_reader = PdfReader(arquivo_pdf)
                    for page in anexo_reader.pages:
                        writer.add_page(page)
            else:
                aviso_buffer = _gerar_pagina_aviso_sem_pdf(resenha)
                aviso_reader = PdfReader(aviso_buffer)
                for page in aviso_reader.pages:
                    writer.add_page(page)

            resenha.gerado_declaracao = True

    if resenhas:
        ResenhaLivro.objects.bulk_update(
            resenhas,
            ['gerado_declaracao', 'atualizado_em']
        )

    output = BytesIO()
    writer.write(output)
    output.seek(0)

    response = HttpResponse(output.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="declaracoes_resenhas_por_aluno.pdf"'
    return response

### Organizacao de resenhas nas pastas por período de leitura ###


def _extrair_texto_primeira_pagina_ocr(caminho_pdf):
    """Extrai o texto da primeira página do PDF usando OCR com pytesseract."""
    documento = pdfium.PdfDocument(str(caminho_pdf))
    try:
        pagina = documento[0]
        imagem = pagina.render(scale=2.8).to_pil()
        texto = pytesseract.image_to_string(imagem, lang='por')
    finally:
        documento.close()

    texto = (texto or '').replace('\r', '')
    texto = re.sub(r'[ \t]+', ' ', texto)
    #print(f"DEBUG - Texto extraído do OCR para '{caminho_pdf.name}':\n{texto}\n")
    #print(40*'*')
    return texto.strip()

def _limpar_linha_ocr(linha):
    """Remove ruídos comuns do OCR no início e no fim da linha."""
    linha = linha.replace('\r', '').strip()
    linha = re.sub(r'^[\|\[\]\*•·:;,_\-\s]+', '', linha)
    linha = re.sub(r'\s+', ' ', linha)
    return linha.strip(' |')


def _extrair_livro_autor_ocr(linhas):
    """Extrai livro e autor a partir do bloco logo após a linha do professor."""
    indice_professor = None

    for indice, linha in enumerate(linhas):
        if 'Professor(a):' in linha:
            indice_professor = indice
            break

    if indice_professor is None:
        return None, None

    candidatos = []
    for linha in linhas[indice_professor + 1:]:
        linha_limpa = _limpar_linha_ocr(linha)
        if not linha_limpa:
            continue
        if re.search(r'Aluno:|Data da Resenha:|Per[ií]odo de Leitura:|Local:', linha_limpa, re.IGNORECASE):
            continue
        if len(linha_limpa) == 1:
            continue
        candidatos.append(linha_limpa)

    if not candidatos:
        return None, None

    nomelivro = candidatos[0]
    nome_autor = None

    for candidato in candidatos[1:]:
        if re.search(r'[A-Za-zÀ-ÿ]{2,}', candidato):
            nome_autor = candidato.rstrip(' .')
            break

    return nomelivro.rstrip(' .'), nome_autor


def _extrair_dados_resenha_ocr(caminho_pdf):
    """Extrai aluno, data da resenha, período, obra e autor da primeira página."""
    texto = _extrair_texto_primeira_pagina_ocr(caminho_pdf)

    if not texto:
        return {
            'sucesso': False,
            'mensagem': 'Nenhum texto foi reconhecido pelo OCR.',
        }

    linhas_brutas = [linha for linha in texto.splitlines() if linha.strip()]
    linhas_limpas = [_limpar_linha_ocr(linha) for linha in linhas_brutas]
    linhas_limpas = [linha for linha in linhas_limpas if linha]
    texto_limpo = '\n'.join(linhas_limpas)    

    aluno_match = re.search(
        r'Aluno:\s*(.+)',
        texto_limpo,
        re.IGNORECASE
    )

    data_periodo_match = re.search(
        r'Data da Resenha:\s*(\d{2}/\d{2}/\d{4})\s*(?:[\|\*N]+\s*)?Per[ií]odo de Leitura:\s*([0-9]{2}/[0-9]{2}\s*a\s*[0-9]{2}/[0-9]{2})',
        texto_limpo,
        re.IGNORECASE
    )

    data_match = re.search(
        r'Data da Resenha:\s*(\d{2}/\d{2}/\d{4})',
        texto_limpo,
        re.IGNORECASE
    )

    periodo_match = re.search(
        r'Per[ií]odo de Leitura:\s*([0-9]{2}/[0-9]{2}\s*a\s*[0-9]{2}/[0-9]{2})',
        texto_limpo,
        re.IGNORECASE
    )

    nomelivro, nomeAutor = _extrair_livro_autor_ocr(linhas_limpas)

    data_resenha = None
    periodo_leitura = None

    if data_periodo_match:
        data_resenha = data_periodo_match.group(1).strip()
        periodo_leitura = data_periodo_match.group(2).strip()
    else:
        if data_match:
            data_resenha = data_match.group(1).strip()
        if periodo_match:
            periodo_leitura = periodo_match.group(1).strip()
   
    if not aluno_match or not data_resenha or not nomelivro:
        return {
            'sucesso': False,
            'mensagem': 'OCR executado, mas os campos padrão não foram encontrados.',
            'texto_extraido': texto_limpo,
        }

    return {
        'sucesso': True,
        'aluno': aluno_match.group(1).strip(),
        'data_resenha': data_resenha,
        'periodo_leitura': periodo_leitura,
        'nomelivro': nomelivro,
        'nomeAutor': nomeAutor,
    }


def _normalizar_nome_arquivo(nome):
    """Normaliza texto para uso em nome de arquivo."""
    nome_normalizado = slugify(nome)
    return nome_normalizado or 'resenha'


def _normalizar_nome_pasta(periodo_leitura):
    """Normaliza o nome da pasta do período."""
    pasta_normalizada = slugify(periodo_leitura)
    return pasta_normalizada or 'periodo-sem-identificacao'


def _buscar_resenha_por_fallback(dados_extraidos, data_resenha):
    """Busca a resenha com critérios progressivos quando o OCR variar entre arquivos."""
    filtros_base = {
        'aluno__nome__iexact': dados_extraidos['aluno'],
        'periodoLeitura__data_resenha': data_resenha,
    }

    combinacoes = [
        {
            **filtros_base,
            'periodoLeitura__intervalo_leitura__iexact': dados_extraidos.get('periodo_leitura'),
            'nomelivro__iexact': dados_extraidos.get('nomelivro'),
            'nomeAutor__iexact': dados_extraidos.get('nomeAutor'),
        },
        {
            **filtros_base,
            'periodoLeitura__intervalo_leitura__iexact': dados_extraidos.get('periodo_leitura'),
            'nomelivro__iexact': dados_extraidos.get('nomelivro'),
        },
        {
            **filtros_base,
            'periodoLeitura__intervalo_leitura__iexact': dados_extraidos.get('periodo_leitura'),
        },
        {
            **filtros_base,
            'nomelivro__iexact': dados_extraidos.get('nomelivro'),
        },
        filtros_base,
    ]

    for combinacao in combinacoes:
        filtros = {
            chave: valor for chave, valor in combinacao.items()
            if valor not in (None, '')
        }

        queryset = (
            ResenhaLivro.objects
            .select_related('aluno', 'periodoLeitura')
            .filter(**filtros)
            .order_by('id')
        )

        resenha = (
            queryset
            .filter(Q(path_resenha__isnull=True) | Q(path_resenha=''))
            .first()
            or queryset.first()
        )

        if resenha:
            return resenha

    return None

@login_required
@require_POST
def organizar_resenhas_por_periodo(request):
    """
    Lê os PDFs escaneados, extrai os dados com OCR, cria a pasta do período,
    renomeia o arquivo com o nome do aluno + id da resenha e atualiza `path_resenha`.
    """
    #path_base = Path('/home/ogliari/Área de trabalho/RESENHAS-BOOT')
    path_base = settings.VAR_DIR_BASE_RESENHA
    path_resenha_analise = path_base / 'scanner'

    status = []

    if not path_resenha_analise.exists():
        status.append({
            'arquivo': str(path_resenha_analise),
            'sucesso': False,
            'mensagem': 'A pasta de análise não foi encontrada.',
        })

        return render(request, 'popup_resultado_organizacao_resenhas.html', {
            'titulo': 'Atualizar resenhas nas pastas',
            'status': status,
            'total_processados': 0,
            'total_sucesso': 0,
            'total_erros': 1,
        })

    arquivos_pdf = sorted(path_resenha_analise.glob('*.pdf'))

    if not arquivos_pdf:
        return render(request, 'popup_resultado_organizacao_resenhas.html', {
            'titulo': 'Atualizar resenhas nas pastas',
            'status': [],
            'total_processados': 0,
            'total_sucesso': 0,
            'total_erros': 0,
        })

    for arquivo_pdf in arquivos_pdf:
        try:
            dados_extraidos = _extrair_dados_resenha_ocr(arquivo_pdf)
        except Exception as exc:
            status.append({
                'arquivo': arquivo_pdf.name,
                'sucesso': False,
                'mensagem': f'Falha ao executar OCR: {exc}',
            })
            continue

        if not dados_extraidos.get('sucesso'):
            status.append({
                'arquivo': arquivo_pdf.name,
                'sucesso': False,
                'mensagem': dados_extraidos.get('mensagem', 'Não foi possível extrair os dados do PDF.'),
            })
            continue

        try:
            data_resenha = datetime.datetime.strptime(
                dados_extraidos['data_resenha'],
                '%d/%m/%Y'
            ).date()
        except ValueError:
            status.append({
                'arquivo': arquivo_pdf.name,
                'sucesso': False,
                'mensagem': f"Data inválida encontrada no OCR: {dados_extraidos['data_resenha']}",
            })
            continue

        resenha = _buscar_resenha_por_fallback(dados_extraidos, data_resenha)

        if not resenha:
            status.append({
                'arquivo': arquivo_pdf.name,
                'sucesso': False,
                'mensagem': (
                    'Nenhuma resenha foi encontrada para '
                    f"aluno '{dados_extraidos['aluno']}', "
                    f"data '{dados_extraidos['data_resenha']}' e "
                    f"período '{dados_extraidos['periodo_leitura']}'."
                ),
            })
            continue

        pasta_periodo = path_base / str(data_resenha.year) / _normalizar_nome_pasta(resenha.periodoLeitura.intervalo_leitura)
        pasta_periodo.mkdir(parents=True, exist_ok=True)

        nome_arquivo = f"{_normalizar_nome_arquivo(resenha.aluno.nome)}-{resenha.id}.pdf"
        destino = pasta_periodo / nome_arquivo

        contador = 1
        while destino.exists():
            destino = pasta_periodo / f"{_normalizar_nome_arquivo(resenha.aluno.nome)}-{resenha.id}-{contador}.pdf"
            contador += 1

        try:
            shutil.move(str(arquivo_pdf), str(destino))
        except Exception as exc:
            status.append({
                'arquivo': arquivo_pdf.name,
                'sucesso': False,
                'mensagem': f'Falha ao mover o arquivo: {exc}',
            })
            continue

        resenha.path_resenha = str(destino)
        resenha.save(update_fields=['path_resenha', 'atualizado_em'])

        status.append({
            'arquivo': arquivo_pdf.name,
            'sucesso': True,
            'mensagem': 'PDF processado, renomeado e vinculado com sucesso.',
            'destino': str(destino),
        })

    total_processados = len(status)
    total_sucesso = len([item for item in status if item['sucesso']])
    total_erros = total_processados - total_sucesso

    return render(request, 'popup_resultado_organizacao_resenhas.html', {
        'titulo': 'Atualizar resenhas nas pastas',
        'status': status,
        'total_processados': total_processados,
        'total_sucesso': total_sucesso,
        'total_erros': total_erros,
        'ano_corrente': datetime.datetime.now().year,
    })