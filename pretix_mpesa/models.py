
from django.db import models
class OnlineCheckout(models.Model):
    """
    Handles Online Checkout
    """
    id = models.BigAutoField(primary_key=True)
    phone = models.BigIntegerField()
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    checkout_request_id = models.CharField(max_length=50, default='')
    account_reference = models.CharField(max_length=50, default='')
    transaction_description = models.CharField(max_length=50, blank=True, null=True)
    customer_message = models.CharField(max_length=100, blank=True, null=True)
    merchant_request_id = models.CharField(max_length=50, blank=True, null=True)
    response_code = models.CharField(max_length=5, blank=True, null=True)
    response_description = models.CharField(max_length=100, blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return str(self.phone)

    class Meta:
        db_table = 'tbl_online_checkout_requests'
        verbose_name_plural = 'Online Checkout Requests'

class OnlineCheckoutResponse(models.Model):
    """
    Handles Online Checkout Response
    """
    id = models.BigAutoField(primary_key=True)
    merchant_request_id = models.CharField(max_length=50, blank=True, null=True)
    checkout_request_id = models.CharField(max_length=50, default='')
    result_code = models.CharField(max_length=5, blank=True, null=True)
    result_description = models.CharField(max_length=100, blank=True, null=True)
    mpesa_receipt_number = models.CharField(max_length=50, blank=True, null=True)
    transaction_date = models.DateTimeField(blank=True, null=True)
    phone = models.BigIntegerField(blank=True, null=True)
    amount = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.phone)

    class Meta:
        db_table = 'tbl_online_checkout_responses'
        verbose_name_plural = 'Online Checkout Responses'