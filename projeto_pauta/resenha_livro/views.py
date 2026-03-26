# /media/ogliari/backup_ssd/projetos-da-cadeia/pauta_pr29/projeto_pauta/resenha_livro/views.py

import os
from django.http import HttpResponse, JsonResponse
from django.templatetags.static import static
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from .models import Aluno, ResenhaLivro, PeriodoLeitura
from .forms import ResenhaLivroForm
from django.contrib.auth.decorators import login_required
from .forms import ResenhaLivroForm, AlunoForm
from django.conf import settings
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
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
    context = {
        'titulo': 'Configurações de Resenhas',
        'ano_corrente': datetime.datetime.now().year,
        'total_alunos': Aluno.objects.count(),
        'total_resenhas': ResenhaLivro.objects.count(),
        'total_periodos': PeriodoLeitura.objects.count(),
    }
    return render(request, 'configuracao_resenhas.html', context)