from django.conf.urls import include, url

from pretix.multidomain import event_url

from .views import confirm , validate
event_patterns = [
    url(r'^mpesa/', include([
        url(r'^confirm/$', confirm, name='confirm'),
        url(r'^validate/$', validate, name='validate'),
         url(r'^callback/$', validate, name='callback')
    ])),
]