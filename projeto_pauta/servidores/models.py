from django.db import models
from django.utils import timezone

from datetime import date

# Create your models here.
class ServidoresPlantao(models.TextChoices):
    PLANTAO_A = 'PLANTAO_A', 'Plantão A'
    PLANTAO_B = 'PLANTAO_B', 'Plantão B'
    PLANTAO_C = 'PLANTAO_C', 'Plantão C'
    PLANTAO_D = 'PLANTAO_D', 'Plantão D'
    ADMINISTRATIVO = 'ADMINISTRATIVO', 'Administrativo'

class Servidores(models.Model):


    nome = models.CharField(
        verbose_name='Nome do servidor',
        max_length=100,
        blank=False,
        null=False
    )
    matricula = models.IntegerField(
        verbose_name='Matrícula do servidor',
        blank=False,
        null=False,
        unique=True
    )
    cpf = models.CharField(
        verbose_name='CPF do servidor',
        max_length=14,
        null=True,
        blank=True,
        unique=True
    )
    ch = models.IntegerField(
        verbose_name='Carga horária semanal',
        blank=False,
        null=False
    )
    setor = models.CharField(
        verbose_name='Setor do servidor',
        choices=ServidoresPlantao.choices,
        blank=False,
        null=False
    )
    
    status_ativo = models.BooleanField(
        verbose_name='Servidor ativo',
        default=True
    )
    def __str__(self):
        return self.nome

    class Meta:
        ordering = ('nome', 'setor',)
        verbose_name = 'servidor'
        verbose_name_plural = 'servidores'



class ServidorFerias(models.Model):
    servidor = models.ForeignKey(
        Servidores,
        on_delete=models.CASCADE,
        verbose_name='Servidor em férias'
    )
    inicio_ferias = models.DateField(
        verbose_name='Início das férias',
        blank=False,
        null=False
    )
    fim_ferias = models.DateField(
        verbose_name='Fim das férias',
        blank=False,
        null=False
    )   

    def esta_de_ferias(self):
        """Verifica se o servidor está de férias hoje"""
        if self.ferias_inicio and self.ferias_fim:
            hoje = date.today()
            return self.ferias_inicio <= hoje <= self.ferias_fim
        return False
    
    def dias_restantes_ferias(self):
        """Retorna quantos dias restam de férias"""
        if self.fim_ferias and self.esta_de_ferias():
            return (self.fim_ferias - date.today()).days
        return 0

    def __str__(self):
        return f'Férias de {self.servidor.nome} de {self.inicio_ferias} a {self.fim_ferias}'

    class Meta:
        ordering = ('servidor', 'inicio_ferias',)
        verbose_name = 'ferias do servidor'
        verbose_name_plural = 'ferias dos servidores'

class ServidorAtestadoMedico(models.Model):
    servidor = models.ForeignKey(
        Servidores,
        on_delete=models.CASCADE,
        verbose_name='Servidor com atestado médico'
    )
    data_inicio = models.DateField(
        verbose_name='Início do atestado médico',
        blank=False,
        null=False
    )
    data_fim = models.DateField(
        verbose_name='Fim do atestado médico',
        blank=False,
        null=False
    )   
    def esta_de_atestado(self):
        """Verifica se o servidor está de atestado médico hoje"""
        if self.data_inicio and self.data_fim:
            hoje = date.today()
            return self.data_inicio <= hoje <= self.data_fim
        return False
    def dias_restantes_atestado(self):
        """Retorna quantos dias restam de atestado médico"""
        if self.data_fim and self.esta_de_atestado():
            return (self.data_fim - date.today()).days
        return 0
    

    def __str__(self):
        return f'Atestado médico de {self.servidor.nome} de {self.data_inicio} a {self.data_fim}'

    class Meta:
        ordering = ('servidor', 'data_inicio',)
        verbose_name = 'atestado médico do servidor'
        verbose_name_plural = 'atestados médicos dos servidores'

class ServidorFolgaCompensatoria(models.Model):
    servidor = models.ForeignKey(
        Servidores,
        on_delete=models.CASCADE,
        verbose_name='Servidor com folga compensatória'
    )
    data_folga = models.DateField(
        verbose_name='Data da folga compensatória',
        blank=False,
        null=False
    )   

    def __str__(self):
        return f'Folga compensatória de {self.servidor.nome} em {self.data_folga}'

    class Meta:
        ordering = ('servidor', 'data_folga',)
        verbose_name = 'folga compensatória do servidor'
        verbose_name_plural = 'folgas compensatórias dos servidores'