from django.conf import settings
import os

QUICKBOOKS_CLIENT_ID = getattr(settings, "QUICKBOOKS_CLIENT_ID", os.getenv(
    'QUICKBOOKS_CLIENT_ID'
))
QUICKBOOKS_CLIENT_SECRET = getattr(settings, 'QUICKBOOKS_CLIENT_SECRET', os.getenv(
    'QUICKBOOKS_CLIENT_SECRET'
))
QUICKBOOKS_REDIRECT_URL = getattr(settings, 'QUICKBOOKS_REDIRECT_URL', "")
QUICKBOOKS_SCOPES = getattr(settings, "QUICKBOOKS_SCOPES", {
    "OPENID": ['openid', 'profile', 'email', 'phone', 'address'],
    "APP": ['com.intuit.quickbooks.accounting', 'com.intuit.quickbooks.payment',
            'openid', 'profile', 'email', 'phone', 'address']
})
QUICKBOOKS_STATE = getattr(settings, 'QUICKBOOKS_STATE', "from-django-server")
QUICKBOOKS_EMAIL_WEBHOOK = getattr(settings, 'QUICKBOOKS_EMAIL_WEBHOOK', None)
# if QUICKBOOKS_EMAIL_WEBHOOK:
#     ALLOWED_HOSTS.append(QUICKBOOKS_EMAIL_WEBHOOK)
DISCOVERY_DOCUMENT = "https://developer.api.intuit.com/.well-known/openid_sandbox_configuration/"
if settings.DEBUG:
    QUICKBOOKS_BASE_URL = 'https://sandbox-quickbooks.api.intuit.com'
else:
    QUICKBOOKS_BASE_URL = 'https://quickbooks.api.intuit.com'
