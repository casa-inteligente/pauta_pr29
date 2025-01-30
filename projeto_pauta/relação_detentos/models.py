# from django.core.validators import MinLengthValidator, MaxLengthValidator, MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone



# Create your models here.
class Relacao(models.Model):
    campo_regime = (
            ('P','Provisório'),
            ('F', 'Fechado'),
            ('SA', 'Semiaberto')
            )
    alocacao_local = (
        ('F', 'Fechado'),
        ('SA', 'Semiaberto')
    )
    IPEN = models.PositiveIntegerField('iPEN')
    nome = models.CharField('Nome', max_length=150)
    comarca = models.CharField('Comarca', max_length=10)
    artigo = models.CharField('Artigo', max_length=8)
    ingresso = models.DateField('Ingresso', default=timezone.now)
    regime = models.CharField('Regime',max_length=2, choices=campo_regime, default="P")
    pena = models.CharField('Pena', max_length=10)
    previsao_saida = models.DateField('Previsão de saída', blank=True, null=True)
    local_alocacao = models.CharField('Local da alocação', choices=alocacao_local, default='F', max_length=2)
    atualizado = models.DateField('Atualizado', default=timezone.now)#colocar atualização padrão na data atual

    def __str__(self):
        return self.nome
    
    def formatted_ingresso(self):
        return self.ingresso.strftime('%d-%m-%y')

    def formatted_previsao_saida(self):
        if self.previsao_saida:
            return self.previsao_saida.strftime('%d-%m-%y')
        return 

    def formatted_atualizado(self):
        return self.atualizado.strftime('%d-%m-%y')

    formatted_ingresso.short_description = 'Ingresso'
    formatted_previsao_saida.short_description = 'Previsão de Saída'
    formatted_atualizado.short_description = 'Atualizado'