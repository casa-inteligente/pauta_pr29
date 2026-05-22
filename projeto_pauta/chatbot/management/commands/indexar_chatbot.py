# chatbot/management/commands/indexar_chatbot.py

from django.core.management.base import BaseCommand

from chatbot.services.indice import indexar_documentos


class Command(BaseCommand):
    help = "Indexa os documentos do chatbot da unidade."

    def handle(self, *args, **options):
        self.stdout.write("Indexando documentos do chatbot...")

        registros = indexar_documentos()

        self.stdout.write(
            self.style.SUCCESS(
                f"Indexação concluída. {len(registros)} trecho(s) indexado(s)."
            )
        )