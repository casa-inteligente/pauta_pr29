import os
from django.http import HttpResponse
from django.templatetags.static import static
from django.shortcuts import render, get_object_or_404, redirect
from .models import Aluno, ResenhaLivro, PeriodoLeitura
from .forms import ResenhaLivroForm
from django.conf import settings
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

def listar_alunos(request):
    # Agrupar alunos por período de leitura
    periodos = PeriodoLeitura.objects.all()
    alunos_por_periodo = {
        periodo: Aluno.objects.filter(resenhas__periodoLeitura=periodo).distinct()
        for periodo in periodos
    }
    return render(request, 'listar_alunos.html', {'alunos_por_periodo': alunos_por_periodo})

def imprimir_resenha(request, aluno_id):
    aluno = get_object_or_404(Aluno.objects.using('resenha_livro'), id=aluno_id)
    resenhas = ResenhaLivro.objects.using('resenha_livro').filter(aluno=aluno)
    linhas = range(50)
    
    return render(request, 'imprimir_resenha.html', {
        'aluno': aluno,
        'resenhas': resenhas,
        'linhas': linhas,
    })


def adicionar_resenha(request):
    if request.method == 'POST':
        form = ResenhaLivroForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('resenha_livro:listar_alunos')
    else:
        form = ResenhaLivroForm()
    return render(request, 'adicionar_resenha.html', {'form': form})

def editar_resenha(request, resenha_id):
    resenha = get_object_or_404(ResenhaLivro.objects.using('resenha_livro'), id=resenha_id)
    if request.method == 'POST':
        form = ResenhaLivroForm(request.POST, instance=resenha)
        if form.is_valid():
            form.save()
            return redirect('resenha_livro:listar_alunos')
    else:
        form = ResenhaLivroForm(instance=resenha)
    return render(request, 'editar_resenha.html', {'form': form})

def gerar_todas_resenhas(request, periodo_id):
    # Obter o período de leitura
    periodo = get_object_or_404(PeriodoLeitura, id=periodo_id)
    resenhas = ResenhaLivro.objects.filter(periodoLeitura=periodo)

    # Criar o PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="resenhas_periodo_{periodo.id}.pdf"'

    # Configurar o canvas do PDF
    pdf = canvas.Canvas(response, pagesize=A4)
    largura, altura = A4

    # Adicionar as resenhas ao PDF
    for resenha in resenhas:
        # Cabeçalho
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(50, altura - 50, "PROJETO REMIÇÃO PELA LEITURA")

        # Tabela do cabeçalho
        pdf.setFont("Helvetica", 12)
        y = altura - 100
        pdf.drawString(50, y, f"Aluno: {resenha.aluno.nome}")
        pdf.drawString(300, y, f"Data da Resenha: {resenha.dataResenha.strftime('%d/%m/%Y')}")
        y -= 20
        pdf.drawString(50, y, f"Período de Leitura: {resenha.periodoLeitura.intervalo_leitura}")
        pdf.drawString(300, y, "Local: CEJA/Ud Presídio Regional de Maravilha")
        y -= 20
        pdf.drawString(50, y, f"Professor(a): {resenha.nomeProfessor}")
        y -= 20
        pdf.drawString(50, y, f"Livro: {resenha.nomelivro}")
        pdf.drawString(300, y, f"Autor: {resenha.nomeAutor}")

        # Linhas para escrita (frente da folha)
        y -= 40
        for _ in range(20):  # 20 linhas por página
            pdf.line(50, y, largura - 50, y)
            y -= 20
            if y < 50:  # Verificar se a página precisa ser trocada
                pdf.showPage()
                pdf.setFont("Helvetica", 12)
                y = altura - 50

        # Adicionar uma nova página para o verso
        pdf.showPage()
        pdf.setFont("Helvetica", 12)

        # Linhas para escrita (verso da folha)
        y = altura - 50
        for _ in range(25):  # 25 linhas no verso
            pdf.line(50, y, largura - 50, y)
            y -= 20
            if y < 50:  # Verificar se a página precisa ser trocada
                pdf.showPage()
                pdf.setFont("Helvetica", 12)
                y = altura - 50

        # Adicionar uma nova página para a próxima resenha
        pdf.showPage()

    # Finalizar o PDF
    pdf.save()
    return response