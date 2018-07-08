
from pretix.base.services.async import ProfiledTask
import pympesa
from pretix.celery_app import app
import logging
logger = logging.getLogger('pretix.plugins.mpesa')
import time

@app.task(base=ProfiledTask)
def send_stk(consumer_key, consumer_secret, business_short_code, password, amount, phone, order_number,callback_url,mode) -> None:
    response = pympesa.oauth_generate_token(consumer_key, consumer_secret,'client_credentials',mode).json()
    access_token = response.get("access_token")
    from pympesa import Pympesa
    mpesa_client = Pympesa(access_token,mode)
    response = mpesa_client.lipa_na_mpesa_online_payment(
        BusinessShortCode=business_short_code,
        Password=password,
        Timestamp=time.strftime('%Y%m%d%H%M%S'),
        TransactionType="CustomerPayBillOnline",
        Amount="100",
        PartyA="254708374149",
        PartyB=business_short_code,
        PhoneNumber=phone,
        CallBackURL='https://nyachoke.localtunnel.me/bigevents/2019/mpesa/callback',
        AccountReference=order_number,
        TransactionDesc=order_number
    )
    logger.debug(response.json())

@app.task(base=ProfiledTask)
def simulate_C2B(consumer_key,consumer_secret):
    response = pympesa.oauth_generate_token(consumer_key, consumer_secret).json()
    access_token = response.get("access_token")
    from pympesa import Pympesa
    mpesa_client = Pympesa(access_token)
    mpesa_client.c2b_simulate_transaction()