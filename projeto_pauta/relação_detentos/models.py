from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.db import models


campo_regime = {'Provisorio',
                'Fechado',
                'Semiaberto',
                }

# Create your models here.
class Relacao(models.Model):
    IPEN = models.PositiveIntegerField('iPEN', validators=[MaxLengthValidator(8), MinLengthValidator(6)])
    nome = models.CharField('Nome', max_length=150)
    artigo = models.CharField('Artigo', max_length=8)
    ingresso = models.DateField('Ingresso')
    #regime = models.CharField('Regime', choices=campo_regime)