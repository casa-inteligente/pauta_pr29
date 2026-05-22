from django.db import models
from django.utils import timezone

from datetime import date
import secrets

# Create your models here.
class ServidoresPlantao(models.TextChoices):
    PLANTAO_A = 'PLANTAO_A', 'Plantão A'
    PLANTAO_B = 'PLANTAO_B', 'Plantão B'
    PLANTAO_C = 'PLANTAO_C', 'Plantão C'
    PLANTAO_D = 'PLANTAO_D', 'Plantão D'
    ADMINISTRATIVO = 'ADMINISTRATIVO', 'Administrativo'
    OUTRAS = 'OUTRAS', 'Outras'

class HorariosExtras(models.TextChoices):
    PRIMEIRO_HORARIO = 'PRIMEIRO_HORARIO', '00h00 às 08h00'
    SEGUNDO_HORARIO = 'SEGUNDO_HORARIO', '08h00 às 16h00'
    TERCEIRO_HORARIO = 'TERCEIRO_HORARIO', '16h00 às 00h00'

class Servidores(models.Model):

    nome = models.CharField(
        verbose_name='Nome:',
        max_length=100,
        blank=False,
        null=False
    )
    sobrenome = models.CharField(
        verbose_name='Sobrenome:',
        max_length=100,
        blank=False,
        null=False
    )

    nome_exibir = models.CharField(
        verbose_name='Nome para exibição',
        max_length=150,
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
        max_length=20,
        blank=False,
        null=False
    )
    cargo = models.CharField(
        verbose_name='Cargo do servidor',
        max_length=100,
        blank=False,
        null=False
    )
    
    status_ativo = models.BooleanField(
        verbose_name='Servidor ativo',
        default=True
    )
    def __str__(self):
        return (f'{self.nome_exibir} - {self.setor}')

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
    observacao_folga = models.TextField(
        verbose_name='Observação da folga compensatória',
        max_length=300,
        blank=True,
        null=True
    )

    def __str__(self):
        return f'Folga compensatória de {self.servidor.nome} em {self.data_folga}'

    class Meta:
        ordering = ('servidor', 'data_folga',)
        verbose_name = 'folga compensatória do servidor'
        verbose_name_plural = 'folgas compensatórias dos servidores'


class ServidoresExtra(models.Model):

    servidor = models.ForeignKey(
        Servidores,
        on_delete=models.CASCADE,
        verbose_name='Plantonista'
    )
    data_extra = models.DateField(
        verbose_name='Data',
        blank=False,
        null=False
    )
    periodo_extra = models.CharField(
        verbose_name='Período do extra',
        choices=HorariosExtras.choices,
        max_length=20,
        blank=False,
        null=False
    )
   
   

    def __str__(self):
        return f'Hora extra de {self.servidor.nome} em {self.data_extra}'

    class Meta:
        ordering = ('data_extra', 'servidor',)
        verbose_name = 'Plantonista extra'
        verbose_name_plural = 'Plantonistas extras'

class UnidadeOficio(models.Model):
    nome = models.CharField(
        verbose_name='Nome da unidade',
        max_length=100,
        blank=False,
        null=False
    )
    sigla = models.CharField(
        verbose_name='Sigla da unidade',
        max_length=6,
        blank=False,
        null=False
    )
    nome_oficio = models.CharField(
        verbose_name='Nome para ofício',
        max_length=10,
        default='PPSC',
        blank=False,
        null=False
    )

    rua = models.CharField(
        verbose_name='Rua da unidade',
        max_length=150,
        default='Rua dos Bobos, 0',
        blank=False,
        null=False
    )
    numero_rua = models.CharField(
        verbose_name='Número da unidade',
        max_length=10,
        default='0',
        blank=False,
        null=False
    )
    bairro = models.CharField(
        verbose_name='Bairro da unidade',
        max_length=100,
        default='Centro',
        blank=False,
        null=False
    )
    cidade = models.CharField(
        verbose_name='Cidade da unidade',
        max_length=100,
        default='Maravilha',
        blank=False,
        null=False
    )
    sigla_uf = models.CharField(
        verbose_name='Sigla do estado da unidade',
        max_length=2,
        default='SC',
        blank=False,
        null=False
    )
    cep_unidade = models.CharField(
        verbose_name='CEP da unidade',
        max_length=9,
        default='00000-000',
        blank=False,
        null=False
    )
    telefone_unidade = models.CharField(
        verbose_name='Telefone da unidade',
        max_length=15,
        default='(00) 0000-0000',
        blank=False,
        null=False
    )
    email_unidade = models.EmailField(
        verbose_name='E-mail da unidade',
        max_length=254,
        default='unidade@pp.sc.gov.br',
        blank=False,
        null=False
    )

    resenha_aprovada = models.BooleanField(
        verbose_name='Resenha aprovada',
        default=True
    )

    # Comarca
    nome_magistrado = models.CharField(
        verbose_name='Nome do magistrado',
        max_length=100,
        default='Dr. Fulano de Tal',
        blank=False,
        null=False
    )

    nome_juizo = models.CharField(
        verbose_name='Nome do juízo',
        max_length=150,
        default='Juiz da 2ª Vara da Comarca de Maravilha/SC',
        blank=False,
        null=False
    )
    def __str__(self):
        return f'{self.nome} ({self.sigla})'

    class Meta:
        ordering = ('nome',)
        verbose_name = 'unidade'
        verbose_name_plural = 'Configurações para ofício'



def gerar_token_gerador_oficio():
    return secrets.token_urlsafe(32)


class LinkGeradorOficio(models.Model):
    token = models.CharField(
        max_length=128,
        unique=True,
        default=gerar_token_gerador_oficio,
        editable=False,
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Link do gerador de ofício"
        verbose_name_plural = "Links do gerador de ofícios"

    def __str__(self):
        return self.token