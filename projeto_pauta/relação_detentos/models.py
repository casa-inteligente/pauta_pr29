from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.db import models




# Create your models here.
class Relacao(models.Model):
    campo_regime = (
            ('P','Provisório'),
            ('F', 'Fechado'),
            ('SA', 'Semiaberto')
                )
    IPEN = models.PositiveIntegerField('iPEN', validators=[MaxLengthValidator(8), MinLengthValidator(6)])
    nome = models.CharField('Nome', max_length=150)
    artigo = models.CharField('Artigo', max_length=8)
    ingresso = models.DateField('Ingresso')
    regime = models.CharField('Regime',max_length=10, choices=campo_regime, default="P")