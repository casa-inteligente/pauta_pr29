from django.db import models
from django.utils import timezone
import re

ANO_CORRENTE = timezone.now().year

class ResenhaLivroManager(models.Manager):
    """ 
    Classe para gerenciar buscas de resenhas de livros
    """
    def search_by_aluno_nome(self, nome_aluno:str, ano=ANO_CORRENTE ):
        """Busca resenhas pelo nome do aluno, ignorando maiúsculas/minúsculas e espaços, e pelo ano."""
        nome_aluno_clean = re.sub(r'\s+', ' ', nome_aluno.strip().lower())
        return self.filter(
            aluno__nome__icontains=nome_aluno_clean,
            periodoLeitura__data_resenha__year=ano
        )
    def search_periodo_leitura(self, periodo_leitura):
        """Busca resenhas pelo período de leitura."""
        return self.filter(
            periodoLeitura__intervalo_leitura__icontains=periodo_leitura
        )
    def search_aprovada(self, aprovada=True):
        """Busca resenhas aprovadas ou não aprovadas."""
        return self.filter(
            aprovada=aprovada
        )
    


class Turma(models.Model):
    """Modelo para turma, sempres sera duas"""
    nome = models.CharField('Nome da Turma:', max_length=100, blank=False, null=False)

    class Meta:
        verbose_name = 'turma'
        verbose_name_plural = 'Adicionar turmas'

    def __str__(self):
        return self.nome

class PeriodoLeitura(models.Model):
    """Modelo para periodo de leitura"""
    turma = models.ForeignKey(
        Turma, 
        on_delete=models.CASCADE, 
        related_name='periodos'
    )
    intervalo_leitura = models.CharField(
        'Periodo de leitura:', 
        max_length=30, 
        blank=False, 
        null=False
    )
    data_resenha = models.DateField('Data da Resenha:', blank=False, null=False)
    aprovada = models.BooleanField(
        'Aprovada:', 
        default=True, 
        blank=False, 
        null=False
    )

    class Meta:
        
        verbose_name = 'periodo de leitura'
        verbose_name_plural = 'Adicionar periodos de leituras'

    def __str__(self):
        return f'{self.turma.nome} - {self.intervalo_leitura}'

class Aluno(models.Model):
    """Modelo para aluno"""
    nome = models.CharField('Nome do Aluno:', max_length=100, blank=False, null=False)
    turma = models.ForeignKey(
        Turma, 
        on_delete=models.CASCADE, 
        related_name='alunos'
    )
    matricula = models.CharField(
        'Matrícula:', 
        max_length=20, 
        unique=True, blank=False, null=True
    )

    class Meta:
        verbose_name = 'aluno'
        verbose_name_plural = 'Adicionar alunos'

    def __str__(self):
        if (self.matricula == None):
            return self.nome
        else:
            return f'{self.nome} - {self.matricula}'

class ResenhaLivro(models.Model):
    """Modelo para resenha de livro"""
    aluno = models.ForeignKey(
        Aluno, 
        on_delete=models.CASCADE, 
        related_name='resenhas'
        )
    nomelivro = models.CharField(
        verbose_name='Obra:', 
        max_length=200, 
        blank=False, null=False
    )
    nomeAutor = models.CharField(
        verbose_name='Autor:', 
        max_length=100, 
        blank=False, null=False
    )
    periodoLeitura = models.ForeignKey(
        PeriodoLeitura, 
        on_delete=models.CASCADE, 
        related_name='resenhas'
    )
    nomeProfessor = models.CharField('Nome do professor(a):', max_length=150, blank=False, null=False, default='Terlene Bolzan')
    aprovada = models.BooleanField('Aprovada', default=True)

    def __str__(self):
        return f'{self.aluno.nome} - {self.nomelivro}'

    @property
    def dataResenha(self):
        """Modelo para data da resenha"""
        return self.periodoLeitura.data_resenha

    #busca no banco de dados personalizada
    objects = ResenhaLivroManager()

    class Meta:
        ordering = ('aluno',)
        verbose_name = 'resenha de livro'
        verbose_name_plural = 'Adicionar resenhas de livros'
        

    def format_data_resenha(self):
        """Modelo para formatar a data da resenha, no modelo"""
        if self.dataResenha:
            return self.dataResenha.strftime('%d/%m/%Y')
    format_data_resenha.short_description = 'Data da Resenha'