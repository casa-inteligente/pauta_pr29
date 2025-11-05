from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from pauta.models import Pauta

class IndexViewTest(TestCase):

    def setUp(self):
        self.pauta = Pauta.objects.create(
            data=timezone.now().date(),
            hora=timezone.now().time(),
            nome="Teste de Pauta",
            situacao="Pendente"
        )

    def test_index_view_status_code(self):
        response = self.client.get(reverse('pauta:index'))
        self.assertEqual(response.status_code, 200)

    def test_index_view_template(self):
        response = self.client.get(reverse('pauta:index'))
        self.assertTemplateUsed(response, 'pauta/index.html')

    def test_index_view_context(self):
        response = self.client.get(reverse('pauta:index'))
        self.assertIn('pautas', response.context)
        self.assertEqual(len(response.context['pautas']), 1)
        self.assertEqual(response.context['pautas'][0], self.pauta)

class PautaAllViewTest(TestCase):

    def setUp(self):
        self.pauta = Pauta.objects.create(
            data=timezone.now().date(),
            hora=timezone.now().time(),
            nome="Teste de Pauta",
            situacao="Pendente"
        )

    def test_pauta_all_view_status_code(self):
        response = self.client.get(reverse('pauta:pauta_all'))
        self.assertEqual(response.status_code, 200)

    def test_pauta_all_view_template(self):
        response = self.client.get(reverse('pauta:pauta_all'))
        self.assertTemplateUsed(response, 'pauta/pauta_all.html')

    def test_pauta_all_view_context(self):
        response = self.client.get(reverse('pauta:pauta_all'))
        self.assertIn('pauta_all', response.context)
        self.assertEqual(len(response.context['pauta_all']), 1)
        self.assertEqual(response.context['pauta_all'][0], self.pauta)