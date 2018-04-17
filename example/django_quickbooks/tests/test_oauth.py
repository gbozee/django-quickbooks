from django.test import TestCase, override_settings
from collections import namedtuple
from quickbooks.models import QuickbooksStorage
from unittest import mock
from quickbooks import QuickbooksAPI
from test.support import EnvironmentVarGuard  # Python>=3


class ModelTestCase(TestCase):
    def setUp(self):
        self.patcher = mock.patch('quickbooks.requests.post')
        self.patcher2 = mock.patch('quickbooks.requests.get')
        self.mock_post = self.patcher.start()
        self.mock_get = self.patcher2.start()
        self.authorize_data = {'token_type': 'bearer', 'access_token': 'eyJlbmMiOiJBMTI4Q0JDLUhTMjU2IiwiYWxnIjoiZGlyIn0..X4zMo3CYEH_E5I6Sa26l8g.fbJBBGYi8mXyn85P0wZk1tMXlMDNuUmQKneJBTAw5i5uuusZCOW0nxBJ1vJGNFjLPCE5R6NpRI-OymEnwJNCkSq7_LNMNqscMhxa8kw4AFZ9qRsZfzuVXDbPO9KKafjUymqFO3oUGWuPOi4UFUECWQdyGqBCrFiJAkSvLLimoM8wsAI2mi8o1GYi-rtu4xslzZMHNDChc8X2NKA4WBG0zXK0sPx_M-DI6l-nCKLuNZ15eLg-OQTmqzfvbYqYWkuHgdR1hnwYzqlDSn1k43sv5ZJGPVmD-Ih01D8rlwdsba8sT5UH9dBIeWA5egDKzQGz4RXZB-1CAKa89wMl_e3dGiD_U1D1Pf0pjHJ1TJ9NdTvB7DH7XZLp_lwwJR8HUY36WZALU85dQpkifpDKS9lUun9V2gDDQ8qe8J_wMRmUtXOexrglH_BKLhdt7QGCUR5hWpG7ZltY5lDRKH0FH7002gLKj77OFn91b0k4in_SZgzq82-iqY3bs4KS1vkz9azOxPDI9kZZrDXTtIAgjkF6zqVP0Csx-RjGJcdT3ic7M2Ex7RGUXs77MU0pE_wsMEDpur-o5eKZrnUzF7TXh-cIjtdm4Cs29Yhcua1gCmdevmypbhGOPxHKZkb0Qxn5kh-1aPgOZFXj-43OmoSKCgcxv8RhaNvbGUkOJGiVV8zs7q-mTMnZjyaF3WbR_e-UNv45.0KYfIXz0CXC98Y9RU_X2Jw', 'expires_in': 3600, 'x_refresh_token_expires_in': 8726400, 'refresh_token': 'Q011532409540WRuIrTP6aZQ7b5QVlbdO6UNYutau5xhdJZJud'}

    def tearDown(self):
        self.patcher.stop()
        self.patcher2.stop()

    def make_api_call(self, callback):
        result = callback()
        return result

    def assert_get_token(self, mock_post, code):
        mock_post.assert_called_with(
            "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer",
            data={'grant_type': 'authorization_code',
                  'redirect_uri': 'http://testserver/quickbooks/auth-response', 'code': code},
            headers={'Accept': 'application/json', 'content-type': 'application/x-www-form-urlencoded', 'Authorization': 'Basic Y2xpZW50X2lkOmNsaWVudF9zZWNyZXQ='})

    def assert_refresh_token(self, mock_post, refresh_token):
        mock_post.assert_called_with(
            "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer",
            data={'grant_type': 'refresh_token',
                  'refresh_token': refresh_token},
            headers={'Accept': 'application/json', 'content-type': 'application/x-www-form-urlencoded', 'Authorization': 'Basic Y2xpZW50X2lkOmNsaWVudF9zZWNyZXQ='})

    def test_oauth_redirect(self):
        self.mock_get.return_value = self.mock_request({
            "issuer": "https://oauth.platform.intuit.com/op/v1",
            "authorization_endpoint": "https://appcenter.intuit.com/connect/oauth2",
            "token_endpoint": "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer",
            "userinfo_endpoint": "https://sandbox-accounts.platform.intuit.com/v1/openid_connect/userinfo",
            "revocation_endpoint": "https://developer.api.intuit.com/v2/oauth2/tokens/revoke",
            "jwks_uri": "https://oauth.platform.intuit.com/op/v1/jwks",
        })
        self.mock_post.return_value = self.mock_request(self.authorize_data)
        self.assertEqual(QuickbooksStorage.objects.count(), 0)

        self.client.get('/quickbooks/auth-response', data={
            'code': "the developer is here",
            'state': 'from-django-server',
            'realmId': "1234"
        })
        self.assert_get_token(self.mock_post, 'the developer is here')

        self.assertEqual(QuickbooksStorage.objects.count(), 1)
        result = QuickbooksStorage.objects.first()
        self.assertEqual(result.access_token,
                         self.authorize_data['access_token'])
        self.assertEqual(result.refresh_token,
                         self.authorize_data['refresh_token'])
        self.assertEqual(result.realmId, '1234')

    def _when_token_not_expired(self, mock_xml, preaction=lambda: None):
        data = QuickbooksStorage.save_token("1234", **self.authorize_data)
        self.assertFalse(data.has_expired())
        preaction()
        self.mock_post.return_value = self.mock_request(mock_xml)
        return QuickbooksAPI("/sample-url")

    def test_create_customer_when_token_not_expired(self):
        api = self._when_token_not_expired('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><IntuitResponse xmlns="http://schema.intuit.com/finance/v3" time="2018-04-17T10:43:55.182-07:00"><Customer domain="QBO" sparse="false"><Id>69</Id><SyncToken>0</SyncToken><MetaData><CreateTime>2018-04-17T10:43:55-07:00</CreateTime><LastUpdatedTime>2018-04-17T10:43:55-07:00</LastUpdatedTime></MetaData><GivenName>danny novak</GivenName><FullyQualifiedName>james@example.com</FullyQualifiedName><DisplayName>james@example.com</DisplayName><PrintOnCheckName>danny novak</PrintOnCheckName><Active>true</Active><PrimaryPhone><FreeFormNumber>+23470322322</FreeFormNumber></PrimaryPhone><PrimaryEmailAddr><Address>james@example.com</Address></PrimaryEmailAddr><DefaultTaxCodeRef>2</DefaultTaxCodeRef><Taxable>true</Taxable><BillAddr><Id>107</Id><Line1>101 igiolugiwej wo</Line1><Country>Nigeria</Country></BillAddr><Job>false</Job><BillWithParent>false</BillWithParent><Balance>0</Balance><BalanceWithJobs>0</BalanceWithJobs><CurrencyRef name="United States Dollar">USD</CurrencyRef><PreferredDeliveryMethod>Print</PreferredDeliveryMethod></Customer></IntuitResponse>')
        sample_data = {
            "email": "james@example.com",
            "full_name": "danny novak",
            "phone_number": "+23470322322",
            "location": {
                "country": "Nigeria",
                "address": "101 igiolugiwej wo",
            }
        }
        response = api.create_customer(**sample_data)
        self.assertEqual(response, {
            'id': '69',
            'name': 'james@example.com'
        })

    def test_create_customer_when_token_not_expired(self):
        api = self._when_token_not_expired('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><IntuitResponse xmlns="http://schema.intuit.com/finance/v3" time="2018-04-17T10:53:44.056-07:00"><SalesReceipt domain="QBO" sparse="false"><Id>147</Id><SyncToken>0</SyncToken><MetaData><CreateTime>2018-04-17T10:53:44-07:00</CreateTime><LastUpdatedTime>2018-04-17T10:53:44-07:00</LastUpdatedTime></MetaData><CustomField><DefinitionId>1</DefinitionId><Name>Crew #</Name><Type>StringType</Type></CustomField><DocNumber>1039</DocNumber><TxnDate>2018-04-17</TxnDate><CurrencyRef name="United States Dollar">USD</CurrencyRef><Line><Id>1</Id><LineNum>1</LineNum><Description>purchased 2 items</Description><Amount>3000.00</Amount><DetailType>SalesItemLineDetail</DetailType><SalesItemLineDetail><ItemRef name="Services">1</ItemRef><UnitPrice>3000</UnitPrice><Qty>1</Qty><TaxCodeRef>NON</TaxCodeRef></SalesItemLineDetail></Line><Line><Amount>3000.00</Amount><DetailType>SubTotalLineDetail</DetailType><SubTotalLineDetail/></Line><TxnTaxDetail><TotalTax>0</TotalTax></TxnTaxDetail><CustomerRef name="james@example.com">69</CustomerRef><BillAddr><Id>107</Id><Line1>101 igiolugiwej wo</Line1><Country>Nigeria</Country></BillAddr><TotalAmt>3000.00</TotalAmt><ApplyTaxAfterDiscount>false</ApplyTaxAfterDiscount><PrintStatus>NeedToPrint</PrintStatus><EmailStatus>NotSet</EmailStatus><Balance>0</Balance><DepositToAccountRef name="Undeposited Funds">4</DepositToAccountRef></SalesReceipt></IntuitResponse>')
        sample_data = {
            'description': "purchased 2 items",
            'price': 3000.00,
            'amount': 3000.00,
            'discount': 0,
            'currency': 'NGN'
        }
        response = api.create_sales_receipt(
            {'id': '69', 'name': 'james@example.com'}, sample_data)
        self.assertEqual(response, '147')

    def mock_request(self, data, status_code=200):
        return MockRequst(data, status_code=status_code)

    def test_refresh_token(self):
        self.mock_get.return_value = self.mock_request({
            "issuer": "https://oauth.platform.intuit.com/op/v1",
            "authorization_endpoint": "https://appcenter.intuit.com/connect/oauth2",
            "token_endpoint": "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer",
            "userinfo_endpoint": "https://sandbox-accounts.platform.intuit.com/v1/openid_connect/userinfo",
            "revocation_endpoint": "https://developer.api.intuit.com/v2/oauth2/tokens/revoke",
            "jwks_uri": "https://oauth.platform.intuit.com/op/v1/jwks",
        })

        sample_data = {'access_token': 'eyJlbmMiOiJBMTI4Q0JDLUhTMjU2IiwiYWxnIjoiZGlyIn0..Jf3JsITu2P6GE4ufb6ElYA.0ZSTcoePtEMg5xHda7RjuMtPFIY93MsC-CU8fjK8kZJRBtYVgX1vCUpeK6IqI6f6QD3DMuzaHDSLWuH4gqXmEsYniYizLQ4eQJwFHyxhiF9jYC_SV7yPd4yUoG1DrhirU0Ujy_Dw02vkMXIJSOEAg4HUWg1CmNEKTvTWn4X5LutJeIt8A2FsSU-Dinlg32HUfftT87GMz7_2IE_do4gfqhQsH2aRIE26n7OPql153JJEgjH-FeCJ6_ZjWbD8T5ZAmDB9MO7xvvqQR8a6Vh9b3ukZ3CqbL7KaejxxiZGM6sGmimT9fhoeaIgVNX5S6x3oDIfZNKtmHiyswOsd_p5aj00tjbBdgQxgasp_Z7TTqzxg04RtS3jgtwIaaApbP3yp-UCTneUU0sL01znql8MUbNL4EXmegBEUtBD_El_C7wr7RAWpNLEwv9pw1hJT9fuXUyxA6P9fwL_I6HCnZDvrer6oCc7-POVQ8kXXE9eMQ1-70AA8-l6vRxj6Pj8xny2_lUWnvZJWxvInQ6aJQGT6tDHaAh60Ipd4P6b6UC2Qtyo6Ld4GQWYnRU4i_VEq32ciY7jYyyelDV-CnWdM2W6CcpTZg8lMVzM5QdoNMerySjzSsadk9q0gmseGCJkkgBi1kxNERam_xXN3urvg0w4HU0lria1nEk0kMlEMPD7XthvWQ4HXAXjT1aRa-YoLukkb.XNZBgw0xILTZylda_g4S3Q',
                       'expires_in': 3600,
                       'refresh_token': 'Q011532713322Pgork3wPLnNTwNOPXsYpvBU8rrkW4W8jNYa8O',
                       'token_type': 'bearer',
                       'x_refresh_token_expires_in': 8721585}
        self.mock_post.return_value = self.mock_request(sample_data)
        data = QuickbooksStorage.save_token("1234", **self.authorize_data)
        api = QuickbooksAPI("/sample-url")
        result = api.save_fetched_token(data)
        self.assert_refresh_token(self.mock_post, data.refresh_token)
        self.assertEqual(result.access_token, sample_data['access_token'])
        self.assertEqual(QuickbooksStorage.objects.count(), 1)


class MockRequst(object):
    def __init__(self, response, **kwargs):
        self.response = response
        self.overwrite = True
        if kwargs.get('overwrite'):
            self.overwrite = True
        self.status_code = kwargs.get('status_code', 200)

    @classmethod
    def raise_for_status(cls):
        pass

    def json(self):
        if self.overwrite:
            return self.response
        return {'data': self.response}

    @property
    def text(self):
        return self.response
