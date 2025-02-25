# from django.core.validators import MinLengthValidator, MaxLengthValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone



# Create your models here.
class Relacao(models.Model):
    
    empresas_conveniadas = (
        ('ROTOPLAST', 'ROTOPLAST'),
        ('CHAMALUX', 'CHAMALUX'),
        ('PREFEITURA', 'PREFEITURA'),
        ('PRESÍDIO', 'PRESÍDIO'),
        ('OLIVEIRA', 'CONS. OLIVEIRA'),
        ('REALCE', 'REALCE'),
        ('SEPAT', 'SEPAT')
    )

    campo_regime = (
            ('PRE', 'Preventiva'),
            ('A', 'Alimentos'),
            ('PRO','Provisório'),
            ('F', 'Fechado'),
            ('SA', 'Semiaberto'),
            ('TOR', 'Tornozeleira')
        )
    alocacao_local = (
        ('F', 'Fechado'),
        ('SA', 'Semiaberto'),
        ('TOR', 'Domiciliar')
    )
    IPEN = models.PositiveIntegerField('iPEN', blank=False, null=False)
    nome = models.CharField('Nome', max_length=150 , blank=False, null=False)
    comarca = models.CharField('Comarca', max_length=50)
    artigo = models.CharField('Artigos', max_length=15)
    ingresso = models.DateField('Ingresso', blank=True, null=True,)
    regime = models.CharField('Regime',max_length=3, choices=campo_regime, blank=True, null=True)
    pena = models.CharField('Pena', max_length=30, blank=True, null=True, default='-')
    previsao_saida = models.DateField('Previsão saída', blank=True, null=True, default=None)
    local_alocacao = models.CharField('Local da alocação', choices=alocacao_local, default='F', max_length=3)
    observacoes = models.CharField('Observações', max_length=150, blank=True, null=True, default='-')
    atualizado = models.DateField('Atualizado', default=timezone.now)
    trampo_empresa = models.CharField('Convênio',max_length=15, choices=empresas_conveniadas, default=None, blank=True, null=True)
    observacoes_trabalho = models.CharField('Observações', max_length=50, blank=True, null=True)

    def __str__(self):
        return self.nome
    
    def save(self, *args, **kwargs):
        if self.regime == 'P':
            self.previsao_saida = None
        super(Relacao, self).save(*args, **kwargs)
    
    class Meta:
        ordering = ('regime', 'nome')
        verbose_name = 'a relação de detentos'
        verbose_name_plural = 'Relações de Detentos'
    
    def formatted_ingresso(self):
        return self.ingresso.strftime('%d-%m-%y')
    formatted_ingresso.short_description = 'Ingresso'

    def formatted_previsao_saida(self):
        if self.previsao_saida:
            return self.previsao_saida.strftime('%d-%m-%y')
       
    formatted_previsao_saida.short_description = 'Previsão de Saída'

    def formatted_atualizado(self):
        return self.atualizado.strftime('%d-%m-%y')    
    formatted_atualizado.short_description = 'Atualizado'

    objetos = models.Manager()#Para buscar os dados atraves do OBJETOS