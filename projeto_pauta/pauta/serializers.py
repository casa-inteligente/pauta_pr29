
from rest_framework import serializers
from .models import Pauta

class PautaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pauta
        fields = ['id', 'data', 'hora', 'nome', 'situacao']
        # Ou especifique os campos: fields = ['id', 'data', 'hora', 'descricao', ...]