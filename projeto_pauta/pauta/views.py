from django.shortcuts import render, redirect
from .models import Pauta
from django.utils import timezone
from datetime import timedelta
from .forms import PautaForm
import datetime


# Imports para API
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import PautaSerializer

# Visualização do dia atual até o terceiro dia seguinte
def index(request):
    today = timezone.now().date()
    end_date = today + timedelta(days=4)
    pautas = Pauta.objects.filter(data__range=[today, end_date]).order_by('data', 'hora')
    return render(request, 'pauta/index.html', {'pautas': pautas})

# Visualização de toda a pauta e inserção de novos compromissos
def pauta_all(request):
    today = timezone.now().date()
    pauta_alls = Pauta.objects.filter(data__gte=today).order_by('data', 'hora')
    
    if request.method == 'POST':
        form = PautaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('pauta:pauta_all')  # Use o namespace 'pauta' aqui
    else:
        form = PautaForm()
    
    return render(request, 'pauta/pauta_all.html', {
        'titulo': 'Pauta',
        'ano_corrente': datetime.datetime.now().year,
        'nome_unidade': 'Presídio Regional de Maravilha',
        'pauta_all': pauta_alls,
        'form': form,
    })


# Visualização do dia atual até o setimo dia seguinte
def index_7(request):
    today = timezone.now().date()
    end_date = today + timedelta(days=7)
    pautas = Pauta.objects.filter(
        data__range=[today, end_date]).order_by('data', 'hora'
    )
    return render(request, 'pauta/index_7.html', {
        'pautas': pautas,
        'titulo': 'Pauta 7 dias',
        'nome_unidade': 'Presídio Regional de Maravilha',
        'ano_corrente': datetime.datetime.now().year,
        }
    )


# ============================================
# API REST - Pauta de 4 dias
# ============================================

@api_view(['GET'])
def api_pauta_4dias(request):
    """
    API que retorna as pautas dos próximos 4 dias
    Endpoint: GET /api/pauta/4dias/
    """
    today = timezone.now().date()
    end_date = today + timedelta(days=4)
    pautas = Pauta.objects.filter(data__range=[today, end_date]).order_by('data', 'hora')
    serializer = PautaSerializer(pautas, many=True)
    
    return Response({
        'success': True,
        'total': pautas.count(),
        'data_inicio': today.isoformat(),
        'data_fim': end_date.isoformat(),
        'pautas': serializer.data
    })


@api_view(['GET'])
def api_pauta_por_data(request):
    """
    API que retorna pautas filtradas por data
    Endpoint: GET /api/pauta/data/?data_inicio=2024-11-01&data_fim=2024-11-30
    """
    data_inicio = request.GET.get('data_inicio', timezone.now().date().isoformat())
    data_fim = request.GET.get('data_fim', (timezone.now().date() + timedelta(days=4)).isoformat())
    
    try:
        pautas = Pauta.objects.filter(
            data__range=[data_inicio, data_fim]
        ).order_by('data', 'hora')
        
        serializer = PautaSerializer(pautas, many=True)
        
        return Response({
            'success': True,
            'total': pautas.count(),
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'pautas': serializer.data
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=400)

# View para renderizar a página de visualização da API
def pauta_api_viewer(request):
    """
    Renderiza uma página HTML com JavaScript para consumir a API
    """
    return render(request, 'pauta/api_viewer.html', {
        'titulo': 'Visualizador de Pauta - API',
        'nome_unidade': 'Presídio Regional de Maravilha',
    })