# /media/ogliari/backup_ssd/projetos-da-cadeia/pauta_pr29/projeto_pauta/resenha_livro/views.py

import os
from io import BytesIO
from pathlib import Path
from django.http import HttpResponse, JsonResponse
from django.templatetags.static import static
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from .models import Aluno, ResenhaLivro, PeriodoLeitura, Turma
from .forms import ResenhaLivroForm, AlunoForm, PeriodoLeituraForm
from django.contrib.auth.decorators import login_required
from django.conf import settings
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from collections import OrderedDict
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from django.db.models import Prefetch
from django.views.decorators.http import require_POST
from pypdf import PdfReader, PdfWriter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import datetime



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


def gerar_todas_resenhas(request, periodo_id):
    """Gerar um PDF com todas as resenhas de um período de leitura."""
    periodo = get_object_or_404(PeriodoLeitura, id=periodo_id)
    resenhas = ResenhaLivro.objects.filter(periodoLeitura=periodo)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="resenhas_periodo_{periodo.id}.pdf"'

    pdf = canvas.Canvas(response, pagesize=A4)
    pdf.setLineWidth(0.5)
    pdf.setStrokeColorRGB(0, 0, 0, 0.7)
    pdf.setAuthor("MRLTech")
    largura, altura = A4

    for resenha in resenhas:
        pdf.setFont("Helvetica-Bold", 16)
        pdf.setLineWidth(0.5)
        pdf.setStrokeColorRGB(0, 0, 0, 0.7)
        titulo = "PROJETO REMIÇÃO PELA LEITURA"
        pdf.drawCentredString(largura / 2, altura - 50, titulo)

        pdf.setFont("Helvetica", 12)
        y = altura - 100
        margem_esquerda = 50
        margem_direita = largura - 50

        pdf.line(margem_esquerda, y + 20, margem_direita, y + 20)
        pdf.line(margem_esquerda, y - 8, margem_direita, y - 8)
        pdf.line(margem_esquerda, y - 25, margem_direita, y - 25)
        pdf.line(margem_esquerda, y - 45, margem_direita, y - 45)
        pdf.line(margem_esquerda, y - 65, margem_direita, y - 65)
        pdf.line(margem_esquerda, y - 85, margem_direita, y - 85)

        pdf.line(margem_esquerda + 280, y - 8, margem_esquerda + 280, y - 45)
        pdf.line(margem_esquerda, y + 20, margem_esquerda, y - 85)
        pdf.line(margem_direita, y + 20, margem_direita, y - 85)

        pdf.drawString(margem_esquerda + 10, y, f"Aluno: {resenha.aluno.nome}")
        y -= 20
        pdf.drawString(margem_esquerda + 10, y, f"Data da Resenha: {resenha.dataResenha.strftime('%d/%m/%Y')}")
        pdf.drawString(margem_direita - 200, y, f"Período de Leitura: {resenha.periodoLeitura.intervalo_leitura}")
        y -= 20
        pdf.drawString(margem_esquerda + 10, y, 'Local: CEJA/Ud Presídio Regional de Maravilha')
        pdf.drawString(margem_direita - 200, y, f"Professor(a): {resenha.nomeProfessor}")

        y -= 20
        pdf.drawCentredString(margem_direita - 250, y, f"{resenha.nomelivro}")
        y -= 20
        pdf.drawString(margem_esquerda + 15, y, f"{resenha.nomeAutor}")

        size_lines = 18
        qtd_linha_1folha = 31
        y -= 40

        pdf.line(margem_esquerda, y, margem_esquerda, y - (size_lines * (qtd_linha_1folha - 1)))
        pdf.line(margem_direita, y, margem_direita, y - (size_lines * (qtd_linha_1folha - 1)))

        for _ in range(qtd_linha_1folha):
            pdf.line(margem_esquerda, y, margem_direita, y)
            y -= size_lines

            if y < 50:
                pdf.showPage()
                pdf.setFont("Helvetica", 12)
                y = altura - 50

        pdf.showPage()
        pdf.setFont("Helvetica", 12)
        y = altura - 50

        qtd_linha_2folha = 40
        pdf.line(margem_esquerda, y, margem_esquerda, y - (size_lines * (qtd_linha_2folha - 1)))
        pdf.line(margem_direita, y, margem_direita, y - (size_lines * (qtd_linha_2folha - 1)))

        for _ in range(qtd_linha_2folha):
            pdf.line(margem_esquerda, y, margem_direita, y)
            pdf.setLineWidth(0.5)
            pdf.setStrokeColorRGB(0, 0, 0, 0.7)

            y -= size_lines
            if y < 50:
                pdf.showPage()
                pdf.setFont("Helvetica", 12)
                y = altura - 50

        pdf.showPage()

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
        fontName='Arial-Bold',
        fontSize=11,
        leading=14,
        alignment=TA_LEFT,
        textColor=colors.black,
        spaceAfter=0,
    )

    estilo_corpo = ParagraphStyle(
        name='CorpoDeclaracao',
        parent=estilos['Normal'],
        fontName='Arial',
        fontSize=11,
        leading=18,
        alignment=TA_JUSTIFY,
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
        "CENTRO DE EDUCAÇÃO DE JOVENS E ADULTOS – CEJA - MH",
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

    texto_declaracao = Paragraph(
        (
            f"Declaramos para os devidos fins de Remição de Pena pela Leitura que o aluno "
            f"<b>{aluno.nome}</b>, matriculado no Centro de Educação de Jovens e Adultos – "
            f"CEJA de MARAVILHA, sob o número de inscrição <b>{numero_matricula}</b>, "
            f"participou do Projeto “Despertar pela Leitura” no Presídio de Maravilha, "
            f"realizando a leitura de <b>{numero_obras}</b> obras, conforme quadro abaixo:"
        ),
        estilo_corpo
    )

    story.append(texto_declaracao)
    story.append(Spacer(1, 16))

    dados_tabela = [[
        Paragraph("N.", estilo_tabela_cabecalho),
        Paragraph("Obra / Autor", estilo_tabela_cabecalho),
        Paragraph("Período", estilo_tabela_cabecalho),
        Paragraph("Resultado", estilo_tabela_cabecalho),
    ]]

    for indice, resenha in enumerate(resenhas, start=1):
        resultado = "Satisfatória" if resenha.aprovada else "Insatisfatória"

        obra_autor = Paragraph(
            f"{resenha.nomelivro} / {resenha.nomeAutor}",
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
        colWidths=[35, 235, 125, 100],
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

    def desenhar_rodape(canvas_obj, doc_obj):
        canvas_obj.saveState()
        canvas_obj.setFont('Arial', 8)
        canvas_obj.setFillColor(colors.HexColor('#6b7280'))
        canvas_obj.drawCentredString(
            A4[0] / 2,
            20,
            "Gerado automaticamente pelo sistema interno"
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