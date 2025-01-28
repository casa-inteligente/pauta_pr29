from django.db import models

# Create your models here.
class Relacao(models.Model):
    IPEN = models.IntegerField('iPEN', max_length=8)
    nome = models.CharField('Nome', max_length=150)
    artigo = models.CharField('Artigo', max_length=80)
    ingresso = models.DateField('Ingresso')
    #regime = models.