
from django.test import TestCase
from pauta.models import Pauta
from datetime import date, time

class PautaModelTest(TestCase):

    def setUp(self):
        self.pauta = Pauta.objects.create(
            data=date(2023, 12, 26),
            hora=time(10, 0),
            nome="Teste de Pauta",
            situacao="Pendente",
            intervalo_repeticao=5,
            numero_repeticoes=3
        )

    def test_pauta_creation(self):
        self.assertTrue(isinstance(self.pauta, Pauta))
        self.assertEqual(self.pauta.__str__(), self.pauta.nome)

    def test_pauta_fields(self):
        self.assertEqual(self.pauta.data, date(2023, 12, 26))
        self.assertEqual(self.pauta.hora, time(10, 0))
        self.assertEqual(self.pauta.nome, "Teste de Pauta")
        self.assertEqual(self.pauta.situacao, "Pendente")
        self.assertEqual(self.pauta.intervalo_repeticao, 5)
        self.assertEqual(self.pauta.numero_repeticoes, 3)