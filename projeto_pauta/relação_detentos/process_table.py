import pdfplumber
import pandas as pd
import os
import django
from django.utils import timezone
import sys


import tabula as tb
# Configurar o Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projeto_pauta.settings')
django.setup()

from relação_detentos.models import Relacao

# Função para mapear o local de alocação
def map_local_alocacao(value):
    mapping = {
        'A': 'F',
        'C': 'F',
        'B': 'SA',
        'D': 'SA',
        'E': 'SA',
    }
    return mapping.get(value, 'F')

# Função para formatar o campo PENA
def format_pena(pena):
    if pena is None or pena == 'N I':
        return ' - '
    pena = pena.replace('\n', ' ')
    anos, meses, dias = 0, 0, 0
    if 'anos' in pena:
        anos = pena.split('anos')[0].strip()
        pena = pena.split('anos')[1].strip()
    if 'meses' in pena:
        meses = pena.split('meses')[0].strip()
        pena = pena.split('meses')[1].strip()
    if 'dias' in pena:
        dias = pena.split('dias')[0].strip()
    
    return f'{anos}A, {meses}M, {dias}D'

# Função para processar o PDF 1.9 e inserir os dados no banco de dados
def process_pdf(file_path):
    #print('Chamou a extração de dados')
    with pdfplumber.open(file_path) as pdf:
        all_tables = []
        for page in pdf.pages:
            tables = page.extract_tables()
            #print(f'\n \n Tabela {page.page_number}: {tables}')
            for table in tables:
                all_tables.append(table)

        if not all_tables:
            #print("Nenhuma tabela encontrada no PDF.")
            return []

        # Primeira tabela fixa [2x6]
        first_table = all_tables[0]
        total_dados = int(first_table[1][5])# obtem a quantidade de detentos
        #print(f'Total de dados: {total_dados} \t\t alocado na memoria: {sys.getsizeof(total_dados)} bytes')

        # Segunda tabela [nX9]
        second_table = all_tables[1]
        df = pd.DataFrame(second_table[1:], columns=second_table[0])  # Ignorar a primeira linha (cabeçalho)

        # Anexar tabelas adicionais à segunda tabela
        for table in all_tables[2:]:
            if len(table) > 0:
                additional_df = pd.DataFrame(table, columns=second_table[0])  # Não ignorar a primeira linha
                df = pd.concat([df, additional_df], ignore_index=True)
                #print(f'Adicionado.......\n\n\n\n\n\n{df}\n\n\n\n')
            #additional_df = pd.DataFrame(table[1:])
            #df = pd.concat([df, additional_df], ignore_index=True)
            #print(f'Adicionado.......\n\n\n\n\n\n{df}\n\n\n\n')

        
        total_dados_apos_index = len(df)
        diferenca_total_dados = total_dados - total_dados_apos_index

        #print(f'Total de linhas após anexar tabelas adicionais: {total_dados_apos_index}\n Total de dados: {total_dados}\n\nA diferença é: {diferenca_total_dados} \t\t\tA tabela esta utilizando: {sys.getsizeof(df)} bytes')

        ##se {diferenca_total_dados} for diferente de zero, possui erro no processamento, e deverá leventar um erro e avisar na tela o usuario

        #if diferenca_total_dados != 0:
            #print('Possui divergencia de informações')
            #raise ValueError('Ao final das concatenações das tabelas esta faltando informações \n\n O pdf gerado esta incompleto na sua concepção ou houve erro na leitura das tabelas.')
            #print('Possui divergencia de informações')

        # Pegar as colunas necessáriasz
        first_col = df.iloc[:, 0].astype(str).reset_index(drop=True) # Coluna que contém IPEN e NOME
        second_col = df.iloc[:, 1].reset_index(drop=True) # Coluna que contém a a situacao penal
        third_col = df.iloc[:, 2].reset_index(drop=True) # Coluna que contém data de ingresso
        fifth_col = df.iloc[:, 4].reset_index(drop=True) # Coluna que contém a alocação
        col_residencia = df.iloc[:, 8].reset_index(drop=True) # Coluna que contém a residencia
        
        #print(f'Residência extraída:\t {col_residencia}')
        #print(f'Local de alocação extraído:\t {fifth_col}')

        added_records = []
        ipens_no_pdf = set()

        for i in range(len(first_col)):
            ipen_nome = first_col[i].split(' ', 1)
            if len(ipen_nome) == 2:
                ipen = int(ipen_nome[0])
                ipens_no_pdf.add(ipen)
                nome = ipen_nome[1].replace('\n', ' ')
                ingresso = pd.to_datetime(third_col[i], format='%d/%m/%Y').date()
                local_alocacao = fifth_col[i]
                local_residencia = col_residencia[i]#Apenas numero
                situacao_penal = second_col[i].replace('\n', ' ')

                # Verificar se o IPEN já está cadastrado
                relacao, created = Relacao.objects.get_or_create(IPEN=ipen, defaults={
                    'nome': nome,
                    'ingresso': ingresso,
                    'local_galeria': local_alocacao, 
                    'local_alocacao': local_alocacao,
                    'local_residencia': local_residencia,
                    'situacao_penal': situacao_penal,
                })

                if created:
                    added_records.append(f'{nome} ({ipen})')
                    #print(f'Registro adicionado: {nome} ({ipen})')
                else:
                    #print(f'Registro já existente: {nome} ({ipen})')
                    #relacao.nome = nome
                    #relacao.ingresso = ingresso
                    relacao.local_galeria = local_alocacao
                    relacao.local_alocacao = local_alocacao
                    relacao.local_residencia = local_residencia
                    relacao.situacao_penal = situacao_penal
                    relacao.atualizado = timezone.now()
                    relacao.save()

        # Remover IPENs que estão no banco de dados, mas não estão no PDF
        ipens_no_banco = set(Relacao.objects.values_list('IPEN', flat=True))
        ipens_a_remover = ipens_no_banco - ipens_no_pdf

        for ipen in ipens_a_remover:
            Relacao.objects.filter(IPEN=ipen).delete()
            #print(f'Registro removido: {ipen}')

    # Excluir o arquivo PDF após o processamento
    os.remove(file_path)
    #print("Arquivo PDF excluído.")
    #print(f'Dados retornados: \t{added_records}')
    return added_records

# Função para processar o PDF e atualizar o campo regime no banco de dados
def process_regime_pdf(file_path):
    #print('Chamou a extração de dados do regime')
    

    tabelas_all = tb.read_pdf(file_path, pages='all')
    #print(f'A quantidade de tabelas é:\t{len(tabelas_all)}')

    tabela_completa = pd.DataFrame()

    for tabela_page in tabelas_all[:-1]:  # Ignorar a última tabela
        tabela_completa = pd.concat([tabela_completa, tabela_page], ignore_index=True)

    #print(tabela_completa)
    """
    Realiza a extração de dados do pdf com a biblioteca pdfplumber
    """
    with pdfplumber.open(file_path) as pdf:
        all_tables = []
  

        for page in pdf.pages:
            tables = page.extract_tables()
            #print(f'\n \n Tabela {page.page_number}: {tables}')  # Imprimir as tabelas para verificação
            text_all = page.extract_text()
            if text_all and not tables:
                pass
                #print(f'Texto sobrando\t\t\t\t{text_all}')
            for table in tables:
                all_tables.append(table)

        if not all_tables:
            #print("Nenhuma tabela encontrada no PDF.")
            return []

        # Remover a última tabela
        all_tables = all_tables[:-1]

        updated_records = []

        # Processar todas as tabelas
        for table in all_tables:
            df = pd.DataFrame(table[1:], columns=table[0])  # Ignorar a primeira linha (cabeçalho)

            # Pegar as colunas necessárias
            first_col = df.iloc[:, 0].astype(str).reset_index(drop=True)  # Coluna que contém IPEN e NOME
            fourth_col = df.iloc[:, 3].reset_index(drop=True)  # Coluna que contém o ARTIGO
            fifth_col = df.iloc[:, 4].reset_index(drop=True)  # Coluna que contém a PENA
            sixth_col = df.iloc[:, 5].reset_index(drop=True)  # Coluna que contém o rgime
            
            i = 0
            while i < len(first_col):
                
                if first_col[i] == 'PRISÃO':
                    regime = 'ALIMENTOS'
                    i += 1
                    ipen_nome = first_col[i].split(' ', 1)
                else:
                    ipen_nome = first_col[i].split(' ', 1)
                    artigo = fourth_col[i]
                    pena = format_pena(fifth_col[i])
                    regime = sixth_col[i]

                if len(ipen_nome) == 2 and ipen_nome[0].isdigit():
                    ipen = int(ipen_nome[0])

                    # Extrair a comarca
                    comarca = None
                    if '|' in df.iloc[i, 2]:
                        comarca_parts = df.iloc[i, 2].split('|')
                        if len(comarca_parts) > 1:
                            comarca = comarca_parts[1].split(',')[0].strip()

                    # Verificar se o IPEN já está cadastrado
                    try:
                        relacao = Relacao.objects.get(IPEN=ipen)
                        relacao.artigo = artigo
                        relacao.pena = pena
                        relacao.comarca = comarca
                        relacao.regime = regime
                        relacao.save()
                        updated_records.append(f'{relacao.nome} ({ipen})')
                        #print(f'Artigo, Pena e Comarca atualizados: {relacao.nome} ({ipen})')
                    except Relacao.DoesNotExist:
                        pass
                        #print(f'IPEN não encontrado: {ipen}')
                else:
                    pass
                    #print(f'Valor inesperado na coluna: {first_col[i]}')

                i += 1

    # Excluir o arquivo PDF após o processamento
    os.remove(file_path)
    #print("Arquivo PDF excluído.")
    #print(f'Dados retornados: \t{updated_records}')
    return updated_records


# Função para extrair a previsão de saída
def exctrai_date_exit(file_path):
    with pdfplumber.open(file_path) as pdf:
        all_tables = []
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                all_tables.append(table)

        if not all_tables:
            #print("Nenhuma tabela encontrada no PDF.")
            return []

        # Remover o cabeçalho da primeira tabela
        first_table = all_tables[0][1:]

        # Anexar tabelas adicionais à primeira tabela
        for table in all_tables[1:]:
            if len(table) > 0:
                first_table.extend(table)

        # Ignorar a última linha da tabela
        first_table = first_table[:-1]

        # Converter a tabela em um DataFrame
        df = pd.DataFrame(first_table)

        # Verificar se as colunas 1 e 2 existem
        if df.shape[1] < 3:
            #print("As colunas 1 e 2 não foram encontradas na tabela.")
            return []

        # Converter as colunas 1 e 2 para datas
        df[4] = pd.to_datetime(df[1], format='%d/%m/%Y', errors='coerce')
        df[2] = pd.to_datetime(df[2], format='%d/%m/%Y', errors='coerce')

        # Encontrar a menor data entre as colunas 1 e 2
        df['min_date'] = df[[4, 2]].min(axis=1)

        # Atualizar o banco de dados com a menor data
        updated_records = []
        for index, row in df.iterrows():
            if pd.notnull(row['min_date']):
                ipen_nome = row[0].split('\n', 1)
                if len(ipen_nome) == 2:
                    ipen = int(ipen_nome[0][:6])  # Pegar os 6 primeiros números como IPEN
                    min_date = row['min_date'].date()
                    other_date = row[4].date() if min_date == row[2].date() else row[2].date()
                    
                    # Verificar se a menor data é anterior a 6 meses da data atual
                    if min_date < (timezone.now().date() - pd.DateOffset(months=6)).date():
                        previsao_saida = other_date
                    else:
                        previsao_saida = min_date
                    
                    # Verificar se o IPEN já está cadastrado
                    try:
                        relacao = Relacao.objects.get(IPEN=ipen)
                        if relacao.previsao_saida != previsao_saida:  # Verifica se precisa atualizar
                            relacao.previsao_saida = previsao_saida
                            relacao.atualizado = timezone.now()
                            #print(f' Atualizado o campo Atualizado em:\t {timezone.now()}')
                            relacao.save()
                        updated_records.append(f'{relacao.nome} ({ipen})')
                    except Relacao.DoesNotExist:
                        pass
                    #print(f'IPEN não encontrado: {ipen}')


    # Excluir o arquivo PDF após o processamento
    os.remove(file_path)
    #print("Arquivo PDF excluído.")
    return updated_records


if __name__ == '__main__':
    '''
    Um pouco mais sofisticado pois depende do django
    '''
    # pdf_file_path = "C:\\Users\\AULA-1\\Documents\\GitHub\\pauta_pr29\\projeto_pauta\\ordem_ingresso.pdf"
    # added_records = process_pdf(pdf_file_path)
    # if added_records:
    #     print('Registros adicionados:')
    #     for record in added_records:
    #         print(record)
    # else:
    #     print("Nenhum registro adicionado.")

    #process_regime_pdf('file_path')