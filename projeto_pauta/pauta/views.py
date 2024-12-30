from django.shortcuts import render
from .models import Pauta
from django.utils import timezone
from datetime import timedelta


# Visualização do dia atual até o terceiro dia seguinte
def index(request):
    today = timezone.now().date()
    end_date = today + timedelta(days=4)
    pautas = Pauta.objects.filter(data__range=[today, end_date]).order_by('data', 'hora')
    return render(request, 'pauta/index.html',{'pautas' : pautas})

#Visualização de toda a pauta
def pauta_all(request):
    today = timezone.now().date()
    pauta_alls = Pauta.objects.filter(data__gte=today.order_by('data', 'hora'))
    return render(request, 'pauta/pauta_all.html', {'pauta_all': pauta_alls}) 