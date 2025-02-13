import pdfplumber
import pandas as pd
import os
import django
from django.utils import timezone

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
    print('Chamou a extração de dados')
    with pdfplumber.open(file_path) as pdf:
        all_tables = []
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                all_tables.append(table)

        if not all_tables:
            print("Nenhuma tabela encontrada no PDF.")
            return []

        # Primeira tabela fixa [2x6]
        first_table = all_tables[0]
        total_dados = int(first_table[1][5])
        print(f'Total de dados: {total_dados}')

        # Segunda tabela [nX9]
        second_table = all_tables[1]
        df = pd.DataFrame(second_table[1:], columns=second_table[0])  # Ignorar a primeira linha (cabeçalho)

        # Anexar tabelas adicionais à segunda tabela
        for table in all_tables[2:]:
            additional_df = pd.DataFrame(table)
            df = pd.concat([df, additional_df], ignore_index=True)

        # Pegar as colunas necessárias
        first_col = df.iloc[:, 0].astype(str).reset_index(drop=True)
        third_col = df.iloc[:, 2].reset_index(drop=True)
        fifth_col = df.iloc[:, 4].reset_index(drop=True)

        added_records = []

        for i in range(len(first_col)):
            ipen_nome = first_col[i].split(' ', 1)
            print(f'A variavél ipen_nome: {ipen_nome[0]} \t {ipen_nome[1]}')
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

    return added_records

if __name__ == '__main__':
    pdf_file_path = "C:\\Users\\AULA-1\\Documents\\GitHub\\pauta_pr29\\projeto_pauta\\ordem_ingresso.pdf"
    added_records = process_pdf(pdf_file_path)
    if added_records:
        print('Registros adicionados:')
        for record in added_records:
            print(record)
    else:
        print("Nenhum registro adicionado.")