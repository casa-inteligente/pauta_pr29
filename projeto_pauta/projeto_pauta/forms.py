from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm


INPUT_CLASSES = (
    "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm "
    "text-slate-800 shadow-sm outline-none transition "
    "focus:border-green-600 focus:ring-2 focus:ring-green-600/20"
)


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ["first_name", "last_name", "email"]
        labels = {
            "first_name": "Nome",
            "last_name": "Sobrenome",
            "email": "E-mail",
        }
        widgets = {
            "first_name": forms.TextInput(attrs={"class": INPUT_CLASSES}),
            "last_name": forms.TextInput(attrs={"class": INPUT_CLASSES}),
            "email": forms.EmailInput(attrs={"class": INPUT_CLASSES}),
        }


class TailwindPasswordChangeForm(PasswordChangeForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)

        labels = {
            "old_password": "Senha atual",
            "new_password1": "Nova senha",
            "new_password2": "Confirme a nova senha",
        }

        for field_name, field in self.fields.items():
            field.label = labels.get(field_name, field.label)
            field.widget.attrs.update({
                "class": INPUT_CLASSES,
                "autocomplete": "current-password" if field_name == "old_password" else "new-password",
            })