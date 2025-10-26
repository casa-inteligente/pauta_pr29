from django import forms
from ..models import DescricaoKitHigiene, Relacao, Descricao_termo_rouparia

from .django_toggle_switch import ToggleSwitchWidget

cor_ativa_toggle = "#C76E00"  # laranjado (Fechado)
cor_inativa_toggle = "#043d09"  # Verde (Semiaberto)

class DescricaoKitHigieneForm(forms.Form):  # Mudança para Form simples
    escolha_tipo_regime = forms.BooleanField(
        label='',  # Label vazio pois já tem no template
        required=False,
        initial=True,  # False = Semiaberto (padrão)
        widget=ToggleSwitchWidget(
            size='sm',
            active_color=cor_ativa_toggle,
            inactive_color=cor_inativa_toggle,
            active_text='Fechado',
            inactive_text='Semiaberto'
        )
    )


# Form específico para rouparia (manter como backup)
class TermoRoupariaForm(forms.Form):
    escolha_tipo_regime = forms.BooleanField(
        label='Tipo de Regime',
        #required=False,
        #initial=False,  # True = Fechado, False = Semiaberto
        widget=ToggleSwitchWidget(
            size='sm',
            active_color=cor_ativa_toggle,
            inactive_color=cor_inativa_toggle,
            active_text='Fechado',
            inactive_text='Semiaberto'
        )
    )