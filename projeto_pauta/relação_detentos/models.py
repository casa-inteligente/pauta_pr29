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
        #max_length=3
    )

    com_higiene = models.BooleanField(
        verbose_name='Com kit de higiene',
        default=True
    )

    def __str__(self):
        return f"Kit {self.numero_kit_roupa}"
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


class CalculoAlimentacao(models.Model):
    """
    Modelo para calcular a quantidade de refeições necessárias para a unidade prisional, com base no número de detentos e no almoço do plantão. 
    """

    # Plantão
    almoco_plantao = models.PositiveBigIntegerField(
        verbose_name='Almoço do plantão',
        blank=False,
        null=False,
        default=0,
    )
    lanche_plantao = models.PositiveBigIntegerField(
        verbose_name='Lanche do plantão',
        blank=False,
        null=False,
        default=0,
    )
    janta_plantao = models.PositiveBigIntegerField(
        verbose_name='Janta do plantão',
        blank=False,
        null=False,
        default=0,
    )
    # Administrativo
    almoco_administrativo = models.PositiveBigIntegerField(
        verbose_name='Almoço do administrativo',
        blank=False,
        null=False,
        default=0,
    )
    lanche_administrativo = models.PositiveBigIntegerField(
        verbose_name='Lanche do administrativo',
        blank=False,
        null=False,
        default=0,
    )

    # Internos
    quantidade_internos_fechado = models.PositiveIntegerField(
        verbose_name='Quantidade de internos no regime fechado',
        blank=False,
        null=False,
        default=0,
    )
    quantidade_internos_semiaberto = models.PositiveIntegerField(
        verbose_name='Quantidade de internos no regime semiaberto',
        blank=False,
        null=False,
        default=0,
    )
    quantidade_internos_custodia = models.PositiveIntegerField(
        verbose_name='Quantidade de internos em custódia',
        blank=False,
        null=False,
        default=0,
    )
    quantidade_internos_pensao = models.PositiveIntegerField(
        verbose_name='Quantidade de internos em pensão alimentícia',
        blank=False,
        null=False,
        default=0,
    )
    quantidade_internos_saida_temporaria = models.PositiveIntegerField(
        verbose_name='Quantidade de internos em saída temporária',
        blank=False,
        null=False,
        default=0,
    )
    # Trabalho externo
    trabalho_externo = models.PositiveIntegerField(
        verbose_name='Quantidade de internos em trabalho externo',
        blank=False,
        null=False,        
        default=0,
    )
    outras_subtracoes = models.PositiveIntegerField(
        verbose_name='Outras subtrações (ex: internos em júri popular, em exames externos, etc.)',
        blank=False,
        null=False,
        default=0,
    )
    internacao_hospitalar = models.PositiveIntegerField(default=0)

    observacoes = models.CharField(
        verbose_name='Observações',
        max_length=200,
        blank=True,
        null=True,
        default='-'
    )


    atualizado_em = models.DateTimeField(
        verbose_name='Atualizado em',
        default=timezone.now
    )



    def __str__(self):
        return f"{self.atualizado_em} atualizado"


    class Meta:
        verbose_name = 'cálculo de alimentação'
        verbose_name_plural = 'Cálculos de alimentação'
        ordering = ('-atualizado_em',)
        get_latest_by = 'atualizado_em'

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
    local_galeria = models.CharField(
        verbose_name='Local da Galeria',
        null=True, blank=True,
        #default='A',
        max_length=1
    )
    local_residencia = models.IntegerField(
        verbose_name='Local de Residência',
        null=True, blank=True        
    )
    situacao_penal = models.CharField(
        verbose_name='Situação penal',
        max_length=20,
        blank=True,
        null=True,
        default='RECOLHIDO(A)'
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
        verbose_name = 'Relação de detentos'
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