from django.test import TestCase
from django.contrib.admin.sites import AdminSite
from pauta.admin import PautaAdmin
from pauta.models import Pauta
from django.utils import timezone

class MockRequest:
    pass

class PautaAdminTest(TestCase):

    def setUp(self):
        self.site = AdminSite()
        self.pauta_admin = PautaAdmin(Pauta, self.site)
        self.pauta = Pauta.objects.create(
            data=timezone.now().date(),
            hora=timezone.now().time(),
            nome="Teste de Pauta",
            situacao="Pendente"
        )

    def test_data_formatada(self):
        formatted_date = self.pauta_admin.data_formatada(self.pauta)
        self.assertEqual(formatted_date, self.pauta.data.strftime('%d/%m/%Y'))

    def test_hora_formatada(self):
        formatted_time = self.pauta_admin.hora_formatada(self.pauta)
        self.assertEqual(formatted_time, self.pauta.hora.strftime('%H:%M'))