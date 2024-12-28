from django.shortcuts import render
from .models import Pauta
from django.utils import timezone
from datetime import timedelta

# Create your views here.
def index(request):
    today = timezone.now().date()
    end_date = today + timedelta(days=4)
    pautas = Pauta.objects.filter(data__range=[today, end_date]).order_by('data', 'hora')
    return render(request, 'pauta/index.html',{'pautas' : pautas})