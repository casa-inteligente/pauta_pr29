from django import forms

from relação_detentos.forms.django_toggle_switch import ToggleSwitchWidget


class ResenhaRemicaoForm(forms.Form):
    resenha_satisfatoria = forms.BooleanField(
        label="Cálculo da remição",
        required=False,
        initial=True,
        widget=ToggleSwitchWidget(
            size="sm",
            active_color="#2ed33c",
            inactive_color="#dc2626",
            active_text="Satisfatória",
            inactive_text="Insatisfatória",
        ),
    )