from django import forms
from ..models import DescricaoKitHigiene, Relacao, Descricao_termo_rouparia

from .django_toggle_switch import ToggleSwitchWidget

cor_ativa_toggle = "#FFA500"  # laranjado (Fechado)
cor_inativa_toggle = "#2ed33c"  # Verde (Semiaberto)

class DescricaoKitHigieneForm(forms.ModelForm):
    class Meta:
        model = Descricao_termo_rouparia  # Corrigido para usar o modelo correto
        fields = ['escolha_tipo_regime']  # Corrigido: remover __all__
        widgets = {
            'escolha_tipo_regime': ToggleSwitchWidget(
                size='sm',
                active_color=cor_ativa_toggle,
                inactive_color=cor_inativa_toggle,
                active_text='Fechado',
                inactive_text='Semiaberto'
            ),
            'com_higiene': forms.CheckboxInput(
                attrs={
                    'class': 'form-checkbox h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500',
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super(DescricaoKitHigieneForm, self).__init__(*args, **kwargs)
        # Não aplicar classes padrão ao toggle switch
        for field_name, field in self.fields.items():
            if field_name == 'escolha_tipo_regime':
                # Manter o widget do toggle switch intacto
                continue
            else:
                field.widget.attrs.update({'class': 'form-control border border-gray-400 rounded'})

# Form específico para rouparia (alternativa mais simples)
class TermoRoupariaForm(forms.Form):
    escolha_tipo_regime = forms.BooleanField(
        label='Tipo de Regime',
        required=False,
        initial=False,  # False = Semiaberto (padrão)
        widget=ToggleSwitchWidget(
            size='sm',
            active_color=cor_ativa_toggle,
            inactive_color=cor_inativa_toggle,
            active_text='Fechado',
            inactive_text='Semiaberto'
        )
    )
    com_higiene = forms.BooleanField(
        label='Incluir Kit Higiene',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(
            attrs={
                'class': 'h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500',
            }
        )
    )