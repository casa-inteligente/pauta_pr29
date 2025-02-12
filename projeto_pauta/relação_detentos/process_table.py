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
    with pdfplumber.open(file_path) as pdf:
        all_tables = []
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                all_tables.append(table)

        df = pd.concat([pd.DataFrame(table) for table in all_tables])

        # Pegar as colunas necessárias
        first_col = df.iloc[:, 0].drop([0, 1, 2]).reset_index(drop=True)
        fourth_col = df.iloc[:, 3].drop([0, 1, 2]).reset_index(drop=True)

        added_records = []

        for i in range(len(first_col)):
            ipen_nome = first_col[i].split('-', 1)
            if len(ipen_nome) == 2:
                ipen = int(ipen_nome[0])
                nome = ipen_nome[1].replace('\n', ' ')
                local_alocacao = map_local_alocacao(fourth_col[i])

                # Verificar se o IPEN já está cadastrado
                relacao, created = Relacao.objects.get_or_create(IPEN=ipen, defaults={
                    'nome': nome,
                    'local_alocacao': local_alocacao,
                    'atualizado': timezone.now()
                })

                if created:
                    added_records.append(f'{nome} ({ipen})')
                    print(f'Registro adicionado: {nome} ({ipen})')
                else:
                    print(f'Registro já existente: {nome} ({ipen})')
        
        #Excluir os arquivos
        os.remove(file_path)

        return added_records

if __name__ == '__main__':
    pdf_file_path = 'caminho/para/seu/arquivo.pdf'
    added_records = process_pdf(pdf_file_path)
    if added_records:
        print('Registros adicionados:')
        for record in added_records:
            print(record)