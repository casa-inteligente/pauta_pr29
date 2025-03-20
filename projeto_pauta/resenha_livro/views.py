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
    pdf.setLineWidth(0.5)#Define a espessura da linha
    pdf.setStrokeColorRGB(0, 0, 0, 0.7)#Define a cor da linhas
    pdf.setAuthor("MRLTech")
    largura, altura = A4

    # Adicionar as resenhas ao PDF
    for resenha in resenhas:
        # Centralizar o título
        pdf.setFont("Helvetica-Bold", 16)
        pdf.setLineWidth(0.5)#Define a espessura da linha
        pdf.setStrokeColorRGB(0, 0, 0, 0.7)#Define a cor da linhas
        titulo = "PROJETO REMIÇÃO PELA LEITURA"
        pdf.drawCentredString(largura / 2, altura - 50, titulo)

        # Tabela do cabeçalho com linhas laterais
        pdf.setFont("Helvetica", 12)
        y = altura - 100
        margem_esquerda = 50
        margem_direita = largura - 50

        # Desenhar as linhas laterais da tabela
        pdf.line(margem_esquerda, y + 20, margem_direita, y + 20)  # Linha superior
        pdf.line(margem_esquerda, y - 8, margem_direita, y - 8)  # Linha professor
        pdf.line(margem_esquerda, y - 25, margem_direita, y - 25)  # Linha professor
        pdf.line(margem_esquerda, y - 45, margem_direita, y - 45)  # Linha professor
        pdf.line(margem_esquerda, y - 65, margem_direita, y - 65)  # Linha autor/obra
        pdf.line(margem_esquerda, y - 85, margem_direita, y - 85)  # Linha inferior

        pdf.line(margem_esquerda + 280 , y - 8, margem_esquerda + 280, y - 45)  # Linha divisoria
        pdf.line(margem_esquerda, y + 20, margem_esquerda, y - 85)  # Linha esquerda
        pdf.line(margem_direita, y + 20, margem_direita, y - 85)  # Linha direita

        # Preencher os dados na tabela
        pdf.drawString(margem_esquerda + 10, y, f"Aluno: {resenha.aluno.nome}")
        y -= 20
        pdf.drawString(margem_esquerda + 10, y, f"Data da Resenha: {resenha.dataResenha.strftime('%d/%m/%Y')}")
        pdf.drawString(margem_direita - 200, y, f"Período de Leitura: {resenha.periodoLeitura.intervalo_leitura}")
        y -= 20
        pdf.drawString(margem_esquerda + 10, y, 'Local: CEJA/Ud Presídio Regional de Maravilha') 
        pdf.drawString(margem_direita - 200, y, f"Professor(a): {resenha.nomeProfessor}")

        y -= 20
        #pdf.drawString(margem_esquerda + 10, y, f"Livro:")
        pdf.drawCentredString(margem_direita - 250, y, f"{resenha.nomelivro}")
        #pdf.drawString(margem_direita - 250, y, f"{resenha.nomelivro}")
        y -= 20
        #pdf.drawString(margem_esquerda + 10, y, f"Autor:")
        pdf.drawString(margem_esquerda + 15, y, f"{resenha.nomeAutor}")


        #ditancia entre linhas
        size_lines = 15
        #quantidade de linhas na primeira folha
        qtd_linha_1folha = 37
        # Linhas para escrita (frente da folha)
        y -= 40
        # Desenhar a linha vertical da esquerda
        pdf.line(margem_esquerda, y, margem_esquerda, y - (size_lines * (qtd_linha_1folha -1)))  # Linha esquerda
        # Desenhar a linha vertical da direita
        pdf.line(margem_direita, y, margem_direita, y - (size_lines * (qtd_linha_1folha -1)))  # Linha direita

        for _ in range(qtd_linha_1folha):  # 20 linhas por página
            pdf.line(margem_esquerda, y, margem_direita, y)
            y -= size_lines

            if y < 50:  # Verificar se a página precisa ser trocada
                pdf.showPage()
                pdf.setFont("Helvetica", 12)
                y = altura - 50

        # Adicionar uma nova página para o verso
        pdf.showPage()
        pdf.setFont("Helvetica", 12)

        # Linhas para escrita (verso da folha)
        y = altura - 50

        #quantidade de linhas na segunda folha
        qtd_linha_2folha = 49
        # Desenhar a linha vertical da esquerda
        pdf.line(margem_esquerda, y, margem_esquerda, y - (size_lines * (qtd_linha_2folha -1)))  # Linha esquerda
        # Desenhar a linha vertical da direita
        pdf.line(margem_direita, y, margem_direita, y - (size_lines * (qtd_linha_2folha -1)))  # Linha direita

        for _ in range(qtd_linha_2folha):  # 49 linhas no verso
            pdf.line(margem_esquerda, y, margem_direita, y)
            pdf.setLineWidth(0.5)#Define a espessura da linha
            pdf.setStrokeColorRGB(0, 0, 0, 0.7)#Define a cor da linhas
            
            y -= size_lines
            if y < 50:  # Verificar se a página precisa ser trocada
                pdf.showPage()
                pdf.setFont("Helvetica", 12)
                y = altura - 50

        # Adicionar uma nova página para a próxima resenha
        pdf.showPage()

    # Finalizar o PDF
    pdf.save()
    return response