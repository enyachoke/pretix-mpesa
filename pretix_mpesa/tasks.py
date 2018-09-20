
from pretix.base.services.tasks import ProfiledTask
from .models import  OnlineCheckout
import base64
import pympesa
import uuid
from pretix.celery_app import app
from decimal import Decimal
import uuid
import logging
logger = logging.getLogger('pretix.plugins.mpesa')
import time

@app.task(base=ProfiledTask)
def send_stk(consumer_key, consumer_secret, business_short_code, password, amount, phone, order_number,callback_url,mode) -> None:
    response = pympesa.oauth_generate_token(consumer_key, consumer_secret,'client_credentials',mode).json()
    access_token = response.get("access_token")
    from pympesa import Pympesa
    mpesa_client = Pympesa(access_token,mode)
    time_stamp = pympesa.generate_timestamp()
    encoded_password = encode_password(shortcode=business_short_code,passkey=password,timestamp=time_stamp)
    response = mpesa_client.lipa_na_mpesa_online_payment(
        BusinessShortCode=business_short_code,
        Password=encoded_password ,
        Timestamp=time_stamp,
        TransactionType="CustomerPayBillOnline",
        Amount=amount,
        PartyA=phone,
        PartyB=business_short_code,
        PhoneNumber=phone,
        CallBackURL=callback_url,
        AccountReference=order_number,
        TransactionDesc=order_number
    )
    json_response = response.json()
    checkout_id = json_response.get('CheckoutRequestID')
    result_code = json_response.get('ResponseCode')
    logger.debug(json_response)
    if result_code == '0':
        OnlineCheckout.objects.create(phone=int(phone),
                                                    amount=Decimal(str(amount)),
                                                    account_reference=order_number,
                                                    checkout_request_id=checkout_id,
                                                    transaction_description=order_number)
        logger.debug('Created request')

@app.task(base=ProfiledTask)
def simulate_C2B(consumer_key,consumer_secret):
    response = pympesa.oauth_generate_token(consumer_key, consumer_secret).json()
    access_token = response.get("access_token")
    from pympesa import Pympesa
    mpesa_client = Pympesa(access_token)
    mpesa_client.c2b_simulate_transaction()

def encode_password(shortcode, passkey, timestamp):
    """Generate and return a base64 encoded password for online access.
    """
    data =  shortcode + passkey + timestamp
    data_bytes = data.encode('utf-8')
    return  base64.b64encode(data_bytes).decode()