import pdfplumber
import pandas as pd
import os
import django
from django.utils import timezone
import sys

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
        'D': 'SA'
    }
    return mapping.get(value, 'F')

# Função para processar o PDF e inserir os dados no banco de dados
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
            print("Nenhuma tabela encontrada no PDF.")
            return []

        # Primeira tabela fixa [2x6]
        first_table = all_tables[0]
        total_dados = int(first_table[1][5])# obtem a quantidade de detentos
        print(f'Total de dados: {total_dados} \t\t alocado na memoria: {sys.getsizeof(total_dados)} bytes')

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

        if diferenca_total_dados != 0:
            print('Possui divergencia de informações')
            raise ValueError('Ao final das concatenações das tabelas esta faltando informações')
            print('Possui divergencia de informações')

        # Pegar as colunas necessárias
        first_col = df.iloc[:, 0].astype(str).reset_index(drop=True) # Coluna que contém IPEN e NOME
        third_col = df.iloc[:, 2].reset_index(drop=True) # Coluna que contém data de ingresso
        fifth_col = df.iloc[:, 4].reset_index(drop=True) # Coluna que contém a alocação

        added_records = []

        for i in range(len(first_col)):
            ipen_nome = first_col[i].split(' ', 1)
            if len(ipen_nome) == 2:
                ipen = int(ipen_nome[0])
                nome = ipen_nome[1].replace('\n', ' ')
                ingresso = pd.to_datetime(third_col[i], format='%d/%m/%Y').date()
                local_alocacao = map_local_alocacao(fifth_col[i])

                # Verificar se o IPEN já está cadastrado
                relacao, created = Relacao.objects.get_or_create(IPEN=ipen, defaults={
                    'nome': nome,
                    'ingresso': ingresso,
                    'local_alocacao': local_alocacao,
                    'atualizado': timezone.now()
                })

                if created:
                    added_records.append(f'{nome} ({ipen})')
                    #print(f'Registro adicionado: {nome} ({ipen})')
                else:
                    pass
                    #print(f'Registro já existente: {nome} ({ipen})')

    # Excluir o arquivo PDF após o processamento
    os.remove(file_path)
    print("Arquivo PDF excluído.")
    #print(f'Dados retornados: \t{added_records}')
    return added_records

# Função para processar o PDF e atualizar o campo regime no banco de dados
def process_regime_pdf(file_path):
    print('Chamou a extração de dados do regime')
    with pdfplumber.open(file_path) as pdf:
        all_tables = []
        for page in pdf.pages:
            tables = page.extract_tables()
            print(f'\n \n Tabela {page.page_number}: {tables}')  # Imprimir as tabelas para verificação
            for table in tables:
                all_tables.append(table)

        if not all_tables:
            print("Nenhuma tabela encontrada no PDF.")
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

            i = 0
            while i < len(first_col):
                if first_col[i] == 'PRISÃO':
                    regime = 'ALIMENTOS'
                    i += 1
                    ipen_nome = first_col[i].split(' ', 1)
                else:
                    ipen_nome = first_col[i].split(' ', 1)
                    artigo = fourth_col[i]
                    pena = fifth_col[i]

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
                        relacao.save()
                        updated_records.append(f'{relacao.nome} ({ipen})')
                        #print(f'Artigo, Pena e Comarca atualizados: {relacao.nome} ({ipen})')
                    except Relacao.DoesNotExist:
                        print(f'IPEN não encontrado: {ipen}')
                else:
                    print(f'Valor inesperado na coluna: {first_col[i]}')

                i += 1

    # Excluir o arquivo PDF após o processamento
    os.remove(file_path)
    print("Arquivo PDF excluído.")
    #print(f'Dados retornados: \t{updated_records}')
    return updated_records


if __name__ == '__main__':
    pdf_file_path = "C:\\Users\\AULA-1\\Documents\\GitHub\\pauta_pr29\\projeto_pauta\\ordem_ingresso.pdf"
    added_records = process_pdf(pdf_file_path)
    if added_records:
        print('Registros adicionados:')
        for record in added_records:
            print(record)
    else:
        print("Nenhum registro adicionado.")
