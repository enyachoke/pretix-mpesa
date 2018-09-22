from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
import logging
import json
from .models import OnlineCheckoutResponse, OnlineCheckout
from pretix.base.models import Order, Quota, RequiredAction,OrderPayment, OrderRefund
from decimal import Decimal

logger = logging.getLogger('pretix.plugins.mpesa')


@csrf_exempt
def confirm(request, *args, **kwargs):
    message = ''


@csrf_exempt
def validate(request, *args, **kwargs):
    message = ''


@csrf_exempt
def stk_callback(request, *args, **kwargs):
    json_data = json.loads(request.body)
    logger.info(json_data)

    try:
        data = json_data.get('Body', {}).get('stkCallback', {})
        update_data = dict()
        update_data['result_code'] = data.get('ResultCode', '')
        update_data['result_description'] = data.get('ResultDesc', '')
        update_data['checkout_request_id'] = data.get('CheckoutRequestID', '')
        update_data['merchant_request_id'] = data.get('MerchantRequestID', '')

        meta_data = data.get('CallbackMetadata', {}).get('Item', {})
        if len(meta_data) > 0:
            # handle the meta data
            for item in meta_data:
                if len(item.values()) > 1:
                    key, value = item.values()
                    if key == 'MpesaReceiptNumber':
                        update_data['mpesa_receipt_number'] = value
                    if key == 'Amount':
                        update_data['amount'] = Decimal(value)
                    if key == 'PhoneNumber':
                        update_data['phone'] = int(value)
                    if key == 'TransactionDate':
                        date = str(value)
                        year, month, day, hour, min, sec = date[:4], date[4:-8], date[6:-6], date[8:-4], date[10:-2], date[12:]
                        update_data['transaction_date'] = '{}-{}-{} {}:{}:{}'.format(year, month, day, hour, min, sec)

        # save
        checkout_request_id = data.get('CheckoutRequestID', '')
        logger.info(dict(updated_data=update_data))
        try:
            online_checkout = OnlineCheckout.objects.get(checkout_request_id=checkout_request_id)
            logger.info('Checkout')
            logger.info(online_checkout.account_reference)
            try:
                payment = OrderPayment.objects.get(id=online_checkout.account_reference)
                logger.info('Payment Found')
                if len(meta_data) > 0:
                    try:
                        payment.confirm()
                    except Quota.QuotaExceededException:
                        pass
            except OrderPayment.DoesNotExist:
                logger.info('Payment Not found')
                pass
        except OnlineCheckout.DoesNotExist:
            logger.info('Not found')
            pass
    except Exception as ex:
        logger.error(ex)
        raise ValueError(str(ex))
    return HttpResponse(request)
