from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

class MinimumNumericPasswordValidator:
    def validate(self, password, user=None):
        if sum(char.isdigit() for char in password) < 4:
            raise ValidationError(
                _("A senha deve conter pelo menos 4 números."),
                code='password_no_enough_numbers',
            )

    def get_help_text(self):
        return _(
            "Sua senha deve conter pelo menos 4 números."
        )