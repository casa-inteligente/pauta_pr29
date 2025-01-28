from django.contrib import admin
from .models import Relacao
from .forms import RelacaoDetentosForm

# Register your models here.
@admin.register(Relacao)
class RelacaoAdmin(admin.ModelAdmin):
    form = RelacaoDetentosForm
    list_display = ('IPEN', 'nome', 'artigo', 'ingresso')
    search_fields = ('nome', "ingresso")