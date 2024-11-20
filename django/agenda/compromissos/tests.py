from django.test import TestCase

# Create your tests here.
class TestarPaginas(TestCase): 
    def testar_se_pagina_principal_carrega_completamente(self): 
        response = self.client.get("/") 
        self.assertEqual(response.status_code, 200) 
        templates_usados = [t.name for t in response.templates] 
        self.assertIn("compromissos/base.html", templates_usados) 
        self.assertIn("compromissos/lista.html", templates_usados) 
        self.assertContains(response, "compromisso")