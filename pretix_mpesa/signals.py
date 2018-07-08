# Register your receivers here
from django.dispatch import receiver
from i18nfield.strings import LazyI18nString

from pretix.base.signals import register_payment_providers 
from pretix.presale.signals import contact_form_fields
from django.utils.translation import ugettext_lazy as _
from django import forms



@receiver(register_payment_providers, dispatch_uid="payment_mpesa")
def register_payment_provider(sender, **kwargs):
    from .payment import Mpesa
    return Mpesa

@receiver(contact_form_fields, dispatch_uid="pretix_mpesa_phone_question")
def add_telephone_question(sender, **kwargs):
    return {'mpesa_phone_number': forms.CharField(
            label=_('Mpesa Phone number'),
            required=sender.settings.telephone_field_required,
            help_text='The payment request will be made to this number by the mpesa payment provider',
            widget=forms.TextInput(attrs={'placeholder': _('Mpesa Phone number')}),
        )}