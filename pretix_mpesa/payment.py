import json
import logging
import urllib.parse
import phonenumbers
import math

from pympesa import Pympesa
from django import forms
from django.contrib import messages
from django.core import signing
from django.template.loader import get_template
from django.utils.translation import ugettext as __, ugettext_lazy as _
from django.utils.functional import cached_property
from collections import OrderedDict
from django.http import HttpRequest

from pretix.base.decimal import round_decimal
from pretix.base.models import Order, Quota, RequiredAction,OrderPayment, OrderRefund
from pretix.base.payment import BasePaymentProvider, PaymentException
from pretix.base.services.mail import SendMailException
from pretix.base.services.orders import mark_order_paid, mark_order_refunded
from pretix.helpers.urls import build_absolute_uri as build_global_uri
from pretix.multidomain.urlreverse import build_absolute_uri
from pretix.plugins.paypal.models import ReferencedPayPalObject
from pretix.presale.views.cart import (
    cart_session, create_empty_cart_id, get_or_create_cart_id,
)
from .tasks import send_stk

logger = logging.getLogger('pretix.plugins.mpesa')


class Mpesa(BasePaymentProvider):
    identifier = 'mpesa'
    verbose_name = _('Mpesa')
    payment_form_fields = OrderedDict([
    ])
    @property
    def abort_pending_allowed(self):
        return False
    @cached_property
    def cart_session(self):
        return cart_session(self.request)

    @property
    def settings_form_fields(self):
        d = OrderedDict(
            [
                ('endpoint',
                 forms.ChoiceField(
                     label=_('Endpoint'),
                     initial='sandbox',
                     choices=(
                         ('production', 'Live'),
                         ('sandbox', 'Sandbox'),
                     ),
                 )),
                ('safaricom_consumer_key',
                 forms.CharField(
                     label=_('Safaricom Consumer Key'),
                     required=True,
                     help_text=_('<a target="_blank" rel="noopener" href="{docs_url}">{text}</a>').format(
                         text=_('Go to the safaricom developer portal to obtain developer keys a get guidance on going live'),
                         docs_url='https://developer.safaricom.co.ke'
                     )
                 )),
                ('safaricom_consumer_secret',
                 forms.CharField(
                     label=_('Safaricom Consumer Secret'),
                     required=True,
                 )),
                ('mpesa_shortcode',
                 forms.CharField(
                     label=_('Lipa na Mpesa Online shortcode'),
                     required=True,
                     help_text=_('Apply for this from safaricom')
                 )),
                ('encryption_password',
                 forms.CharField(
                     label=_('Encription Password'),
                     required=True,
                     help_text=_('The password for encrypting the request')
                 )),
                 ('stk_callback_url',
                 forms.CharField(
                     label=_('Mpesa STK Callback'),
                     required=True,
                     help_text=_('This is the callback url for mpesa stk')
                 )),
                ('mpesa_phone_number_field_required',
                 forms.BooleanField(
                     label=_('Will the mpesa phone number be required to place an order'),
                     help_text=_("If this is not checked, entering a mpesa phone number is optional and the mpesa payment my not work."),
                     required=False,
                 )),

            ] + list(super().settings_form_fields.items())
        )
        return d

    def checkout_confirm_render(self, request) -> str:
        """
        Returns the HTML that should be displayed when the user selected this provider
        on the 'confirm order' page.
        """
        template = get_template('pretix_mpesa/checkout_payment_confirm.html')
        ctx = {'request': request, 'event': self.event, 'settings': self.settings}
        return template.render(ctx)

    def order_pending_render(self, request, order) -> str:
        template = get_template('pretix_mpesa/pending.html')
        ctx = {'request': request, 'event': self.event, 'settings': self.settings, 'order': order}
        return template.render(ctx)

    def payment_form_render(self, request) -> str:
        template = get_template('pretix_mpesa/checkout_payment_form.html')
        ctx = {'request': request, 'event': self.event, 'settings': self.settings}
        return template.render(ctx)

    def checkout_prepare(self, request, cart):
        self.request = request
        mpesa_phone_number = self.cart_session.get('contact_form_data', {}).get('mpesa_phone_number', '')
        try:
            parsed_num = phonenumbers.parse(mpesa_phone_number, 'KE')
        except phonenumbers.NumberParseException:
            messages.error(request, _('Please check to confirm that you entered the mpesa phone number and that it was a valid phone number'))
            return False
        else:
            if phonenumbers.is_valid_number(parsed_num):
                request.session['mpesa_phone_number'] = '254' + str(parsed_num.national_number)
                return True
            else:
                messages.error(request, _('The Mpesa number is not a valid phone number'))
                return False

    def payment_is_valid_session(self, request):
        return True

    def order_can_retry(self, order):
        return self._is_still_available(order=order)

    def execute_payment(self, request: HttpRequest, payment: OrderPayment):
        """
        Will be called if the user submitted his order successfully to initiate the
        payment process.

        It should return a custom redirct URL, if you need special behavior, or None to
        continue with default behavior.

        On errors, it should use Django's message framework to display an error message
        to the user (or the normal form validation error messages).

        :param order: The order object
        """
        kwargs = {}
        if request.resolver_match and 'cart_namespace' in request.resolver_match.kwargs:
            kwargs['cart_namespace'] = request.resolver_match.kwargs['cart_namespace']
        parsed_num = request.session.get('mpesa_phone_number', '')
        logger.debug(parsed_num)
        mode = self.settings.get('endpoint')
        consumer_key = self.settings.get('safaricom_consumer_key')
        consumer_secret = self.settings.get('safaricom_consumer_secret')
        business_short_code = self.settings.get('mpesa_shortcode')
        password = self.settings.get('encryption_password')
        amount = math.ceil(payment.amount)
        callback_url = self.settings.get('stk_callback_url')
        logger.debug(amount)
        logger.debug(callback_url)
        send_stk.apply_async(kwargs={'consumer_key': consumer_key, 'consumer_secret': consumer_secret,
                                     'business_short_code': business_short_code,
                                     'password': password, 'amount': str(amount), 'phone': parsed_num, 'order_number': str(payment.id),
                                     'callback_url': callback_url, 'mode': mode})
        return None
