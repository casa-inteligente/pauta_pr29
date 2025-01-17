from django.db import models

# Create your models here.
class Pauta(models.Model):
    data = models.DateField('Data*')
    hora = models.TimeField('Hora*')
    nome = models.CharField('Nome*', max_length=200)
    situacao = models.TextField('Situação*')
    intervalo_repeticao = models.IntegerField("Intervalo de repetição em DIAS", null=True, blank=True)
    numero_repeticoes = models.IntegerField("Número de repetições", null=True, blank=True)

    def __str__(self):
        return self.nome