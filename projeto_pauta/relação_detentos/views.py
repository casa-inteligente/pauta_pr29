
import pdfplumber
import pandas as pd
import json
import datetime
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, FileResponse, HttpResponse
from django.core.files.storage import FileSystemStorage
from .models import Relacao
from django.db.models import Case, When, Value
from django.db.models.functions import Concat
from django.utils import timezone
from .process_table import process_pdf, process_regime_pdf, exctrai_date_exit
from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.generic import NameObject, createStringObject
import io 
import os

@login_required
def add_detento(request):
    '''
    Responsavel pela adicão de novos cadastros
    '''
    if request.method == 'POST':
        IPEN = request.POST.get('IPEN')
        nome = request.POST.get('nome')
        comarca = request.POST.get('comarca')
        artigo = request.POST.get('artigo')
        ingresso = request.POST.get('ingresso')
        regime = request.POST.get('regime')
        pena = request.POST.get('pena', '-')
        local_alocacao = request.POST.get('local_alocacao')
        previsao_saida = request.POST.get('previsao_saida')
        observacao = request.POST.get('observacao')
        atualizado = request.POST.get('atualizado')

        # Converter datas para o formato correto
        ingresso = datetime.datetime.strptime(ingresso, '%Y-%m-%d').date()
        if previsao_saida:
            previsao_saida = datetime.datetime.strptime(previsao_saida, '%Y-%m-%d').date()
        else:
            previsao_saida = None
        if atualizado:
            atualizado = datetime.datetime.strptime(atualizado, '%Y-%m-%d').date()
        else:
            atualizado = None

        # Criar novo registro no banco de dados
        Relacao.objects.create(
            IPEN=IPEN,
            nome=nome,
            comarca=comarca,
            artigo=artigo,
            ingresso=ingresso,
            regime=regime,
            pena=pena,
            local_alocacao=local_alocacao,
            previsao_saida=previsao_saida,
            observacoes=observacao,
            atualizado=atualizado
        )

        return redirect('relação_detentos:relacao_list')

    return render(request, 'relacao_list.html')

@login_required
def relacao_list(request):

    '''
    responsavél por processaro os dados e exibir na página
    '''
    regime_order = Case(
        When(regime='PRO', then=Value(1)),
        When(regime='PRE', then=Value(2)),
        When(regime='F', then=Value(3)),
        When(regime='SA', then=Value(4)),
    )

    relacoes = Relacao.objects.all().annotate(
        regime_order=regime_order
    ).order_by('regime_order', 'previsao_saida', 'local_alocacao', 'nome')

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
    qtd_preventiva = 0
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
    Responsavél por salvar as informações alteradas na página inicial
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


@login_required
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


@login_required
def cadastro_trampo_view(request):
    detento = None
    ipen = request.GET.get('ipen')
    if ipen:
        try:
            detento = Relacao.objects.get(IPEN=ipen)
        except Relacao.DoesNotExist:
            detento = None
    return render(request, 'cadastro_trampo.html', {'detento': detento})


@login_required
def gerar_termo_autorizacao(request, detento_id):
    # Busca o detento no banco de dados
    detento = get_object_or_404(Relacao, id=detento_id)

    # Prepara os dados para preencher o PDF
    dados = {
        'nome': detento.nome,
        'ipen': str(detento.IPEN),
        'comarca': detento.comarca or 'Não informada',
        'artigo': detento.artigo,
        'regime': detento.get_regime_display() if hasattr(detento, 'get_regime_display') else detento.regime,
        'empresa': detento.get_trampo_empresa_display() if hasattr(detento, 'get_trampo_empresa_display') else (detento.trampo_empresa or ''),
        'observacoes': detento.observacoes_trabalho or '',
        # Adicione outros campos conforme o PDF
    }

    # Caminho do PDF modelo (ajuste conforme o local real do arquivo)
    input_pdf_path = os.path.join(settings.BASE_DIR, 'doc', 'Termo de autorização.pdf')
    if not os.path.exists(input_pdf_path):
        return HttpResponse("Arquivo do termo de autorização não encontrado.", status=404)

    # Sobrescreve o arquivo original com os dados preenchidos
    with open(input_pdf_path, "rb") as original_pdf:
        output_stream = io.BytesIO()
        preencher_campos_pdf(original_pdf, output_stream, dados)
        output_stream.seek(0)
        # Salva o PDF preenchido sobrescrevendo o original
        with open(input_pdf_path, "wb") as f:
            f.write(output_stream.getvalue())
        output_stream.seek(0)

    # Retorna o arquivo sobrescrito para download
    response = FileResponse(output_stream, as_attachment=True, filename='termo_autorizacao.pdf')
    return response

def preencher_campos_pdf(input_pdf_file, output_stream, dados):
    reader = PdfReader(input_pdf_file)
    writer = PdfWriter()

    # Copia todas as páginas
    for page in reader.pages:
        writer.add_page(page)

    # Preenche os campos do formulário (os nomes das chaves de 'dados' devem ser iguais aos campos do PDF)
    writer.update_page_form_field_values(
        writer.pages[0],  # supondo que os campos estão na primeira página
        dados
    )

    # Torna os campos somente leitura
    for j in range(len(writer.pages)):
        page = writer.pages[j]
        if '/Annots' in page:
            for annot in page['/Annots']:
                annot_obj = annot.get_object()
                annot_obj.update({
                    NameObject("/Ff"): 1
                })

    writer.write(output_stream)