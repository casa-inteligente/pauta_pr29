from django.test import TestCase
from pauta.forms import PautaForm

class PautaFormTest(TestCase):

    def test_pauta_form_valid(self):
        form = PautaForm(data={
            'nome': "Teste de Pauta",
            'data': "2023-12-26",
            'hora': "10:00:00",
            'situacao': "Pendente",
            'intervalo_repeticao': 5,
            'numero_repeticoes': 3
        })
        self.assertTrue(form.is_valid())

    def test_pauta_form_invalid(self):
        form = PautaForm(data={})
        self.assertFalse(form.is_valid())