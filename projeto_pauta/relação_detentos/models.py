# from django.core.validators import MinLengthValidator, MaxLengthValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

class Descricao_termo_rouparia(models.Model):
    descricao_fechado = models.CharField(
        verbose_name='Descrição da rouparia do Fechado',
        max_length=200,
        blank=False,
        null=False
    )
    descricao_semiaberto = models.CharField(
        verbose_name='Descrição da rouparia do Semiaberto',
        max_length=200,
        blank=False,
        null=False
    )
    escolha_tipo_regime = models.BooleanField(
        verbose_name='Escolha o tipo de regime Fechado ou Semiaberto',
        default=True
    )
    numero_kit_roupa = models.PositiveIntegerField(
        verbose_name='Número do kit de roupa',
        blank=False,
        null=False,
        default=0,
        max_length=3
    )

    com_higient = models.BooleanField(
        verbose_name='Com kit de higiene',
        default=True
    )
    
    def __str__(self):
        return self.numero_kit_roupa

    class Meta:
        ordering = ('numero_kit_roupa',)
        verbose_name = 'descrição do termo de rouparia'
        verbose_name_plural = 'Descrições do termo de rouparia'


class DescricaoKitHigiene(models.Model):
    descricao = models.CharField(
        verbose_name='Descrição do item',
        max_length=200,
        blank=False,
        null=False
    )
    checked_data_recebido = models.BooleanField(
        verbose_name='Data recebido, preenchido',
        default=False
    )
    checked_kit_higiene = models.BooleanField(
        verbose_name='Kit de higiene, com "X"',
        default=True
    )

    def __str__(self):
        return self.descricao

    class Meta:
        ordering = ('descricao',)
        verbose_name = 'descrição do kit de higiene'
        verbose_name_plural = 'Descrições do kit de higiene'

# Create your models here.
class Relacao(models.Model):
   
    empresas_conveniadas = (
        ('ROTOPLAST', 'ROTOPLAST'),
        ('BRUNA', 'BRUNA MALHAS'),
        ('PREFEITURA', 'PREFEITURA'),
        ('PRESÍDIO', 'PRESÍDIO'),
        ('OLIVEIRA', 'CONSTRUTORA OLIVEIRA'),
        ('REALCE', 'FOGÕES REALCE'),
        ('SEPAT', 'SEPAT'),
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
    IPEN = models.PositiveIntegerField(
        verbose_name='iPEN', 
        blank=False, null=False
    )
    nome = models.CharField(
        verbose_name='Nome',
        max_length=150, 
        blank=False, null=False
    )
    comarca = models.CharField(
        verbose_name='Comarca',
        max_length=50,
        default='NI',
        null=True,
        blank=True
    )
    artigo = models.CharField(
        verbose_name='Artigos',
        max_length=15
    )
    ingresso = models.DateField(
        verbose_name='Ingresso',
        blank=True,
        null=True
    )
    regime = models.CharField(
        verbose_name='Regime',
        max_length=3,
        choices=campo_regime,
        blank=True,
        null=True
    )
    pena = models.CharField(
        verbose_name='Pena',
        max_length=30,
        blank=True,
        null=True,
        default='-'
    )
    previsao_saida = models.DateField(
        verbose_name='Previsão saída',
        blank=True,
        null=True,
        default=None
    )
    local_alocacao = models.CharField(
        verbose_name='Local da alocação',
        choices=alocacao_local,
        default='F',
        max_length=3
    )
    observacoes = models.CharField(
        verbose_name='Observações',
        max_length=150,
        blank=True,
        null=True,
        default='-'
    )
    atualizado = models.DateField(
        verbose_name='Atualizado',
        default=timezone.now
    )
    trampo_empresa = models.CharField(
        verbose_name='Convênio',
        max_length=15,
        choices=empresas_conveniadas,
        default=None,
        blank=True,
        null=True
    )
    observacoes_trabalho = models.CharField(
        verbose_name='Observações',
        max_length=50,
        blank=True,
        null=True
    )

    def __str__(self):
        return f'{self.IPEN}-{self.nome}'

    def save(self, *args, **kwargs):
        if self.regime == 'P':
            self.previsao_saida = None
        super(Relacao, self).save(*args, **kwargs)
    
    class Meta:
        ordering = ('regime', 'nome', 'IPEN')
        #db_table = 'relacao_detentos'
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

    objects = models.Manager()#Para buscar os dados atraves do OBJETOS