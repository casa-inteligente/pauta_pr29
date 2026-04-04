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

# def process_pdf_1_8(file_path):
#     with pdfplumber.open(file_path) as pdf:
#         all_tables = []

#         for page in pdf.pages:
#             tables = page.extract_tables()
#             for table in tables:
#                 if table:
#                     all_tables.append(table)

#         if len(all_tables) < 2:
#             os.remove(file_path)
#             return []

#         quantidades_tabelas = len(all_tables)
        

#         total_internos = all_tables[0][1][4]
#         print(f'Total de internos: {total_internos}\n\n')

#         tabela_internos = all_tables[1]
#         colunas = tabela_internos[0]

#         df = pd.DataFrame(tabela_internos[1:], columns=colunas)

#         for tabela in all_tables[2:]:
#             if not tabela:
#                 continue

#             linhas = tabela

#             if tabela[0] == colunas:
#                 linhas = tabela[1:]

#             df_tabela = pd.DataFrame(linhas, columns=colunas)
#             df = pd.concat([df, df_tabela], ignore_index=True)

#         #print(f'Tabela de internos:\n\n{df}')

#         primeira_col = df.iloc[:, 0].astype(str).reset_index(drop=True)   # PRONTUÁRIO | NOME
#         segunda_col = df.iloc[:, 1].reset_index(drop=True)                # SITUAÇÃO
#         terceira_col = df.iloc[:, 2].reset_index(drop=True)               # ALA
#         quarta_col = df.iloc[:, 3].reset_index(drop=True)                 # GAL.
#         quinta_col = df.iloc[:, 4].reset_index(drop=True)                 # BLOCO
#         sexta_col = df.iloc[:, 5].reset_index(drop=True)                  # PISO
#         setima_col = df.iloc[:, 6].reset_index(drop=True)                 # TIPO RESID.
#         oitava_col = df.iloc[:, 7].reset_index(drop=True)                 # RESID.


#         print(f"As colunas extraídas foram:\n\n{primeira_col}\n\n{segunda_col}\n\n{terceira_col}\n\n{quinta_col}\n\n{oitava_col}")

#         registros_processados = []
#         ipens_no_pdf = set()
#     os.remove(file_path)
#     return registros_processados

def process_pdf_1_8(file_path):
    with pdfplumber.open(file_path) as pdf:
        all_tables = []
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                if table:
                    all_tables.append(table)

        if len(all_tables) < 2:
            os.remove(file_path)
            return []

        # Primeira tabela = resumo
        first_table = all_tables[0]
        total_internos = int(str(first_table[1][4]).replace('\n', ' ').strip())
        print(f'Total de internos: {total_internos}')

        # Segunda tabela = dados com cabeçalho
        second_table = all_tables[1]
        colunas = second_table[0]

        linhas_iniciais = []
        for linha in second_table[1:]:
            linha = list(linha or [])
            if len(linha) < len(colunas):
                linha.extend([None] * (len(colunas) - len(linha)))
            elif len(linha) > len(colunas):
                linha = linha[:len(colunas)]
            linhas_iniciais.append(linha)

        df = pd.DataFrame(linhas_iniciais, columns=colunas)

        # Demais tabelas = continuação, normalmente sem cabeçalho
        for table in all_tables[2:]:
            if len(table) > 0:
                linhas = table

                if table[0] == colunas:
                    linhas = table[1:]

                linhas_normalizadas = []
                for linha in linhas:
                    linha = list(linha or [])
                    if len(linha) < len(colunas):
                        linha.extend([None] * (len(colunas) - len(linha)))
                    elif len(linha) > len(colunas):
                        linha = linha[:len(colunas)]
                    linhas_normalizadas.append(linha)

                additional_df = pd.DataFrame(linhas_normalizadas, columns=colunas)
                df = pd.concat([df, additional_df], ignore_index=True)

        total_dados_apos_index = len(df)
        diferenca_total_dados = total_internos - total_dados_apos_index

        print(f'Total extraído: {total_dados_apos_index}')
        print(f'Diferença do resumo: {diferenca_total_dados}')

        if df.shape[1] < 8:
            os.remove(file_path)
            return []

        # Colunas do PDF 1.8
        first_col = df.iloc[:, 0].astype(str).reset_index(drop=True)   # PRONTUÁRIO | NOME
        second_col = df.iloc[:, 1].reset_index(drop=True)              # SITUAÇÃO
        third_col = df.iloc[:, 2].reset_index(drop=True)               # ALA
        fourth_col = df.iloc[:, 3].reset_index(drop=True)              # GAL.
        fifth_col = df.iloc[:, 4].reset_index(drop=True)               # BLOCO
        sixth_col = df.iloc[:, 5].reset_index(drop=True)               # PISO
        seventh_col = df.iloc[:, 6].reset_index(drop=True)             # TIPO RESID.
        eighth_col = df.iloc[:, 7].reset_index(drop=True)              # RESID.

        registros_processados = []
        ipens_no_pdf = set()

        for i in range(len(first_col)):
            texto_ipen_nome = str(first_col[i]).replace('\n', ' ').strip()

            if ' - ' in texto_ipen_nome:
                ipen_nome = texto_ipen_nome.split(' - ', 1)
            elif '-' in texto_ipen_nome:
                ipen_nome = texto_ipen_nome.split('-', 1)
            else:
                print(f'Linha ignorada: {texto_ipen_nome}')
                continue

            if len(ipen_nome) != 2:
                print(f'Linha ignorada: {texto_ipen_nome}')
                continue

            ipen_txt = ipen_nome[0].strip()
            nome = ipen_nome[1].strip()

            if not ipen_txt.isdigit():
                print(f'Linha ignorada: {texto_ipen_nome}')
                continue

            ipen = int(ipen_txt)
            ipens_no_pdf.add(ipen)

            situacao_penal = str(second_col[i]).replace('\n', ' ').strip() if pd.notna(second_col[i]) else 'RECOLHIDO(A)'
            ala = str(third_col[i]).replace('\n', ' ').strip() if pd.notna(third_col[i]) else ''
            galeria = str(fourth_col[i]).replace('\n', ' ').strip() if pd.notna(fourth_col[i]) else ''
            bloco = str(fifth_col[i]).replace('\n', ' ').strip() if pd.notna(fifth_col[i]) else ''
            piso = str(sixth_col[i]).replace('\n', ' ').strip() if pd.notna(sixth_col[i]) else ''
            tipo_residencia = str(seventh_col[i]).replace('\n', ' ').strip() if pd.notna(seventh_col[i]) else ''
            residencia_txt = str(eighth_col[i]).replace('\n', ' ').strip() if pd.notna(eighth_col[i]) else ''

            local_alocacao = map_local_alocacao(galeria)
            regime = 'A' if galeria == 'E' else local_alocacao

            try:
                local_residencia = int(residencia_txt) if residencia_txt else None
            except ValueError:
                local_residencia = None

            observacoes = f'ALA: {ala} | BLOCO: {bloco} | PISO: {piso} | TIPO: {tipo_residencia}'

            relacao, created = Relacao.objects.get_or_create(
                IPEN=ipen,
                defaults={
                    'nome': nome,
                    'artigo': 'NI',
                    'ingresso': None,
                    'regime': regime,
                    'pena': '-',
                    'local_galeria': galeria or None,
                    'local_alocacao': local_alocacao,
                    'local_residencia': local_residencia,
                    'situacao_penal': situacao_penal or 'RECOLHIDO(A)',
                    'observacoes': observacoes,
                }
            )

            if not created:
                relacao.nome = nome
                relacao.regime = regime
                relacao.local_galeria = galeria or None
                relacao.local_alocacao = local_alocacao
                relacao.local_residencia = local_residencia
                relacao.situacao_penal = situacao_penal or 'RECOLHIDO(A)'
                relacao.observacoes = observacoes
                relacao.atualizado = timezone.now()
                relacao.save()

            registros_processados.append(f'{nome} ({ipen})')

        # Remove registros que estão no banco, mas não vieram no PDF atual
        ipens_no_banco = set(Relacao.objects.values_list('IPEN', flat=True))
        ipens_a_remover = ipens_no_banco - ipens_no_pdf

        for ipen in ipens_a_remover:
            Relacao.objects.filter(IPEN=ipen).delete()

    os.remove(file_path)
    return registros_processados


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