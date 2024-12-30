from django.test import SimpleTestCase
from django.urls import reverse, resolve
from pauta.views import index

class UrlsTest(SimpleTestCase):

    def test_index_url_is_resolved(self):
        url = reverse('index')
        self.assertEqual(resolve(url).func, index)