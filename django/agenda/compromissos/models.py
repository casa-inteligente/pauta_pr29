# compromissos/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import datetime

class Compromisso(models.Model):
    data = models.DateField()
    horario = models.TimeField(default=datetime.time(9, 0))
    nome = models.CharField(max_length=200)
    situacao = models.CharField(max_length=200, default='A verificar')
    adicionado_por = models.ForeignKey(User, on_delete=models.CASCADE, default='1')

    def __str__(self):
        return f"{self.nome} ({self.data} às {self.horario})"
    

