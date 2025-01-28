from django.contrib import admin
from .models import Relacao

# Register your models here.
@admin.register(Relacao)
class RelacaoAdmin(admin.ModelAdmin):
    pass