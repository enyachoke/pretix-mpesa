from django.conf.urls import include, url

from pretix.multidomain import event_url

from .views import confirm , validate , stk_callback
event_patterns = [
    url(r'^mpesa/', include([
        url(r'^confirm/$', confirm, name='confirm'),
        url(r'^validate/$', validate, name='validate'),
         url(r'^callback/$', stk_callback, name='callback')
    ])),
]