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

    ferias_inicio = models.DateField(
        verbose_name='Início das férias',
        null=True,
        blank=True
    )
    ferias_fim = models.DateField(
        verbose_name='Fim das férias',
        null=True,
        blank=True
    )

    atestado_medico = models.DateField(
        verbose_name='Servidor com atestado médico',
        null=True,
        blank=True
    )
    folga_compensatoria = models.DateField(
        verbose_name='Servidor com folga compensatória',
        null=True,
        blank=True
    )
    
    status_ativo = models.BooleanField(
        verbose_name='Servidor ativo',
        default=True
    )


    def esta_de_ferias(self):
        """Verifica se o servidor está de férias hoje"""
        if self.ferias_inicio and self.ferias_fim:
            hoje = date.today()
            return self.ferias_inicio <= hoje <= self.ferias_fim
        return False
    
    def dias_restantes_ferias(self):
        """Retorna quantos dias restam de férias"""
        if self.ferias_fim and self.esta_de_ferias():
            return (self.ferias_fim - date.today()).days
        return 0
    
    def __str__(self):
        return self.nome

    class Meta:
        ordering = ('nome', 'setor',)
        verbose_name = 'servidor'
        verbose_name_plural = 'servidores'