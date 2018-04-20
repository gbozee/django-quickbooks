from django.urls import path
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.shortcuts import reverse
from django.views.decorators.csrf import csrf_exempt
from . import QuickbooksAPI, settings
from django.conf import settings as django_settings
from .models import QuickbooksStorage


def quickbooks_auth_response(request):
    url = request.build_absolute_uri(reverse('quickbooks:code'))
    if not django_settings.DEBUG:
        url = url.replace('http://','https://')
    hub = QuickbooksAPI(url)
    code = request.GET.get('code')
    error = request.GET.get('error')
    state = request.GET.get('state')
    realm_id = request.GET.get('realmId')
    if state != settings.QUICKBOOKS_STATE:
        return HttpResponseBadRequest("This is a bad request")
    response = {
        'code': code,
        'error': error,
        'state': state,
        'realm_id': realm_id
    }
    response, status = hub.get_token(code)
    if status < 400:
        QuickbooksStorage.save_token(realm_id, **response)
    response.update(status=status)
    return JsonResponse(response)


def quickbooks_authorize(request):
    hub = QuickbooksAPI(request.build_absolute_uri(reverse('quickbooks:code')))

    return HttpResponse('''
    <a href="{}"><img src="https://developer.intuit.com/docs/@api/deki/files/4996/c2qb_green_btn_med_default.png?revision=1&size=bestfit&width=103&height=35"/></a>
    '''.format(hub.get_authorization_url()))


urlpatterns = [
    path('auth-response', quickbooks_auth_response, name="code"),
    path('authorize', quickbooks_authorize, name="authorize"),
]
