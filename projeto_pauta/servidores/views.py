from django.shortcuts import render, get_object_or_404, redirect
from .models import Servidores, ServidorFerias, ServidorAtestadoMedico, ServidorFolgaCompensatoria, ServidoresExtra
from django.http import HttpResponse
from datetime import date, timedelta
import calendar

def lista_escala_servidores(request):
    ano_corrente = date.today().year
    mes_corrente = date.today().month
    
    # Obter o número de dias do mês
    num_dias_mes = calendar.monthrange(ano_corrente, mes_corrente)[1]
    
    # Lista dos plantões em ordem
    plantoes = ['A', 'B', 'C', 'D']
    
    # Nomes dos dias da semana
    dias_semana = [
        'segunda-feira', 'terça-feira', 'quarta-feira', 
        'quinta-feira', 'sexta-feira', 'sábado', 'domingo'
    ]
    
    # Obter servidores por plantão (ativos)
    servidores_por_plantao = {}
    for plantao in ['PLANTAO_A', 'PLANTAO_B', 'PLANTAO_C', 'PLANTAO_D']:
        servidores_por_plantao[plantao] = Servidores.objects.filter(
            setor=plantao,
            status_ativo=True
        )
    
    # Gerar dados da escala
    escala_dados = []
    
    for dia in range(1, num_dias_mes + 1):
        data_dia = date(ano_corrente, mes_corrente, dia)
        
        # Determinar o plantão do dia (A, B, C, D em ciclo)
        plantao_indice = (dia - 1) % 4
        plantao_dia = plantoes[plantao_indice]
        plantao_key = f'PLANTAO_{plantao_dia}'
        
        # Obter dia da semana
        dia_semana_num = data_dia.weekday()  # 0=segunda, 6=domingo
        nome_dia_semana = dias_semana[dia_semana_num]
        
        # Servidores do plantão que estão disponíveis
        servidores_disponiveis = []
        for servidor in servidores_por_plantao.get(plantao_key, []):
            # Verificar se não está de férias
            em_ferias = ServidorFerias.objects.filter(
                servidor=servidor,
                inicio_ferias__lte=data_dia,
                fim_ferias__gte=data_dia
            ).exists()
            
            # Verificar se não está com atestado
            com_atestado = ServidorAtestadoMedico.objects.filter(
                servidor=servidor,
                data_inicio__lte=data_dia,
                data_fim__gte=data_dia
            ).exists()
            
            # Verificar se não está de folga compensatória
            de_folga = ServidorFolgaCompensatoria.objects.filter(
                servidor=servidor,
                data_folga=data_dia
            ).exists()
            
            if not (em_ferias or com_atestado or de_folga):
                servidores_disponiveis.append(servidor.nome)
        
        # Obter extras por horário
        extras_primeiro = ServidoresExtra.objects.filter(
            data_extra=data_dia,
            periodo_extra='PRIMEIRO_HORARIO'
        ).values_list('servidor__nome', flat=True)
        
        extras_segundo = ServidoresExtra.objects.filter(
            data_extra=data_dia,
            periodo_extra='SEGUNDO_HORARIO'
        ).values_list('servidor__nome', flat=True)
        
        extras_terceiro = ServidoresExtra.objects.filter(
            data_extra=data_dia,
            periodo_extra='TERCEIRO_HORARIO'
        ).values_list('servidor__nome', flat=True)
        
        escala_dados.append({
            'dia': dia,
            'nome_dia_semana': nome_dia_semana,
            'plantao': plantao_dia,
            'servidores': ', '.join(servidores_disponiveis),
            'extras_primeiro': ', '.join(extras_primeiro),
            'extras_segundo': ', '.join(extras_segundo),
            'extras_terceiro': ', '.join(extras_terceiro),
            'data': data_dia,
        })
    
    contexto = {
        'escala_dados': escala_dados,
        'ano_corrente': ano_corrente,
        'mes_corrente': mes_corrente,
        'nome_mes': calendar.month_name[mes_corrente],
    }
    return render(request, 'escala_servidores.html', contexto)