from django import forms
from .models import Pauta
from bleach import clean

class PautaForm(forms.ModelForm):
    class Meta:
        model = Pauta
        fields = '__all__'
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date'}),
            'hora': forms.TimeInput(attrs={'type': 'time', 'class' : 'time-input'}),  # Alterar para o widget padrão de hora
            'intervalo_repeticao' : forms.NumberInput(attrs={'min': 1, 'placeholder': 'Dias'}),
            'numero_repeticoes' : forms.NumberInput(attrs={'min': 1, 'placeholder': 'Número de Repetições'}),
        }

    def clean_situacao(self):
        value = self.cleaned_data['situacao']
        allowed_tags = [
            'p', 'b', 'i', 'u', 'a', 'ul', 'li', 'br', 'span', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'font', 'color', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'em', 'blockquote', 'pre', 'code', 'hr', 'ol', 'dl', 'dt', 'dd', 'caption', 'img', 'video', 'audio', 'iframe', 'embed', 'object', 'param', 'source', 'canvas', 'svg', 'path', 'circle', 'rect', 'line', 'polygon', 'polyline', 'g', 'use', 'defs', 'style', 'script', 'noscript', 'section', 'article', 'aside', 'header', 'footer', 'nav', 'main', 'figure', 'figcaption', 'time', 'mark', 'abbr', 'cite', 'dfn', 'kbd', 'samp', 'var', 'sub', 'sup', 'strikethrough', 'backquote', 'hr', 'del', 'ins', 'small', 'big', 'wbr', 's', 'bdi', 'bdo', 'ruby', 'rt', 'rp',
        ]  # Tags HTML permitidas
        allowed_attrs = {
            'a': ['href', 'target', 'title'],  # Atributos permitidos para links
            'p': ['style'],  # Permitir estilos inline para parágrafos
            'span': ['style'],  # Permitir estilos inline para coloração
            'table': ['border', 'cellpadding', 'cellspacing'],  # Atributos para tabelas
            'th': ['colspan', 'rowspan'],  # Atributos para células de cabeçalho
            'td': ['colspan', 'rowspan'],  # Atributos para células de tabela
            'img': ['src', 'alt', 'width', 'height'],  # Atributos para imagens
            'video': ['src', 'controls', 'autoplay', 'loop', 'muted'],  # Atributos para vídeos
            'audio': ['src', 'controls', 'autoplay', 'loop', 'muted'],  # Atributos para áudio
            'iframe': ['src', 'width', 'height', 'frameborder', 'allowfullscreen'],  # Atributos para iframes
            'embed': ['src', 'type', 'width', 'height'],  # Atributos para embeds
            'object': ['data', 'type', 'width', 'height'],  # Atributos para objetos
            'param': ['name', 'value'],  # Atributos para parâmetros de objetos
            'source': ['src', 'type'],  # Atributos para fontes de mídia
            'canvas': ['width', 'height'],  # Atributos para canvas
            'div': ['class', 'id'],  # Atributos para divs
            'h1': ['class', 'id'],  # Atributos para cabeçalhos
            'h2': ['class', 'id'],  # Atributos para cabeçalhos
            'h3': ['class', 'id'],  # Atributos para cabeçalhos
            'h4': ['class', 'id'],  # Atributos para cabeçalhos
            'h5': ['class', 'id'],  # Atributos para cabeçalhos
            'h6': ['class', 'id'],  # Atributos para cabeçalhos
            'font': ['color', 'size', 'face'],  # Atributos para fonte
            'color': ['style'],  # Permitir estilos inline para coloração
            'strong': ['style'],  # Permitir estilos inline para negrito
            'em': ['style'],  # Permitir estilos inline para itálico
            'blockquote': ['style'],  # Permitir estilos inline para citações
            'pre': ['style'],  # Permitir estilos inline para pré-formatado
            'code': ['style'],  # Permitir estilos inline para código
            'backquote': ['style'],  # Permitir estilos inline para citações
            'hr': ['style'],  # Permitir estilos inline para linha horizontal
            'strikethrough': ['style'],  # Permitir estilos inline para texto riscado
        }
        return clean(value, tags=allowed_tags, attributes=allowed_attrs)
