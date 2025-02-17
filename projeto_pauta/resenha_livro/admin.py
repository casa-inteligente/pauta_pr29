from django.contrib import admin
from .models import ResenhaLivro

# Register your models here.
@admin.register(ResenhaLivro)
class Resenha(admin.ModelAdmin):
    list_display = ('format_data_resenha', 'nomeAluno', 'nomelivro')

