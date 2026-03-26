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
from django.db.models import Prefetch
from django.views.decorators.http import require_POST
from pypdf import PdfReader, PdfWriter
import datetime


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


def _gerar_declaracao_pdf_bytes(resenha):
    """Gera o PDF da declaração em memória."""
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    largura, altura = A4

    resultado_resenha = 'satisfatória' if resenha.aprovada else 'insatisfatória'

    pdf.setTitle(f"Declaracao_{resenha.aluno.nome}")
    pdf.setAuthor("Sistema Pauta")

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawCentredString(largura / 2, altura - 70, "DECLARAÇÃO")

    pdf.setFont("Helvetica", 12)
    texto = pdf.beginText(70, altura - 130)
    texto.setLeading(22)

    linhas = [
        f"Declaro, para os devidos fins, que o(a) aluno(a) {resenha.aluno.nome}",
        f"participou do Projeto Remição pela Leitura no período {resenha.periodoLeitura.intervalo_leitura},",
        f"com resenha referente à obra \"{resenha.nomelivro}\", de autoria de {resenha.nomeAutor}.",
        "",
        f"Resultado da avaliação da resenha: {resultado_resenha}.",
        f"Data da resenha: {resenha.dataResenha.strftime('%d/%m/%Y')}",
        f"Professor(a): {resenha.nomeProfessor}",
        f"Turma: {resenha.aluno.turma.nome}",
        "",
        "Documento emitido automaticamente pelo sistema.",
    ]

    for linha in linhas:
        texto.textLine(linha)

    pdf.drawText(texto)

    pdf.line(70, 180, largura - 70, 180)
    pdf.setFont("Helvetica", 11)
    pdf.drawCentredString(largura / 2, 160, "Presídio Regional de Maravilha")

    pdf.showPage()
    pdf.save()
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
    """Gera PDF único com declaração + anexo da resenha, quando existir."""
    ids = request.POST.getlist('resenhas_ids')

    resenhas = list(
        ResenhaLivro.objects
        .filter(id__in=ids)
        .select_related('aluno', 'aluno__turma', 'periodoLeitura')
        .order_by('aluno__turma__nome', 'aluno__nome', '-periodoLeitura__data_resenha')
    )

    writer = PdfWriter()

    for resenha in resenhas:
        declaracao_buffer = _gerar_declaracao_pdf_bytes(resenha)
        declaracao_reader = PdfReader(declaracao_buffer)
        for page in declaracao_reader.pages:
            writer.add_page(page)

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
        #resenha.atualizado_por = request.user

    if resenhas:
        ResenhaLivro.objects.bulk_update(
            resenhas,
            ['gerado_declaracao', 'atualizado_em']
        )

    output = BytesIO()
    writer.write(output)
    output.seek(0)

    response = HttpResponse(output.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="declaracoes_resenhas.pdf"'
    return response