from django.core.validators import MinLengthValidator, MaxLengthValidator, MinValueValidator, MaxValueValidator
from django.db import models


# Modelo para Pena
class Pena(models.Model):
    ano = models.PositiveIntegerField('Ano', default=1)
    mes = models.PositiveIntegerField('Mês', validators=[MinValueValidator(0), MaxValueValidator(12)], default=1)
    dias = models.PositiveIntegerField('Dias', validators=[MinValueValidator(0), MaxValueValidator(31)], default=1)

    def __str__(self):
        return f"{self.ano} anos, {self.mes} meses, {self.dias} dias"


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
    #pena = models.OneToOneField(Pena, on_delete=models.CASCADE)

    def __str__(self):
        return self.nome