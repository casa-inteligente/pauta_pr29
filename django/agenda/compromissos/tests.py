from django.test import TestCase
from django.urls import reverse

# Create your tests here.
class TestarPaginas(TestCase): 
    def testar_se_pagina_principal_carrega_completamente(self): 
        response = self.client.get("/") 
        self.assertEqual(response.status_code, 200) 
        templates_usados = [t.name for t in response.templates] 
        self.assertIn("compromissos/base.html", templates_usados) 
        self.assertIn("compromissos/lista.html", templates_usados) 
        self.assertContains(response, "compromisso")

    def testar_pagina_ajuda_carrega(self):
        response = self.client.get(reverse("pagina_ajuda"))
        self.assertEqual(response.status_code, 200) 
        self.assertTemplateUsed(response, 'compromissos/ajuda.html')
        self.assertContains(response, "<h2>Ajuda</h2>")