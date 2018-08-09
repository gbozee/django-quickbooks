# -*- coding: utf-8 -*-
# from __future__ import unicode_literals
from builtins import super, str, int
from future.standard_library import install_aliases

install_aliases()
from . import settings
import requests
from urllib.parse import urlparse, urlencode, quote
import base64
from xml.etree import ElementTree
import logging

logger = logging.getLogger(__name__)


def stringToBase64(s):
    return base64.b64encode(bytes(s, "utf-8")).decode()


class QuickbooksAPIException(Exception):
    pass


class QuickbooksAPI(object):
    def __init__(self, *args):
        self.client_id = settings.QUICKBOOKS_CLIENT_ID
        self.client_secret = settings.QUICKBOOKS_CLIENT_SECRET
        self.redirect_url = settings.QUICKBOOKS_REDIRECT_URL
        self.base_url = settings.QUICKBOOKS_BASE_URL
        self.call_url = self.base_url
        self.view_url = self.redirect_url
        if not self.client_id and self.client_secret and self.redirect_url:
            raise QuickbooksAPIException(
                (
                    "Please remember to set the QUICKBOOKS_CLIENT_ID "
                    "AND QUICKBOOKS_CLIENT_SECRET env"
                )
            )

    def get_authorization_url(self):
        path = self.auth_path("/connect/oauth2")
        scope = quote("com.intuit.quickbooks.accounting")
        return "{}?redirect_uri={}&client_id={}&response_type=code&scope={}&state={}".format(
            path, self.redirect_url, self.client_id, scope, settings.QUICKBOOKS_STATE
        )

    def auth_path(self, path):
        return "https://appcenter.intuit.com" + path

    def _get_token_details(self, grant_type, param):
        options = {
            "authorize": ("authorization_code", "code", "token_endpoint"),
            "refresh": ("refresh_token", "refresh_token", "token_endpoint"),
        }
        authorization_header = "Basic " + stringToBase64(
            self.client_id + ":" + self.client_secret
        )
        data = options[grant_type]
        params = {
            "grant_type": data[0],
            "redirect_uri": self.redirect_url,
            data[1]: param,
        }
        if data[0] == "refresh_token":
            params.pop("redirect_uri")
        headers = {
            "Accept": "application/json",
            "content-type": "application/x-www-form-urlencoded",
            "Authorization": authorization_header,
        }
        url = self.discovery_document["token_endpoint"]
        response = self.make_request("POST", url, data=params, headers=headers)
        if response.status_code >= 400:
            print(response.json())
            print(params)
            response.raise_for_status()
        return response.json(), response.status_code

    def get_token(self, code):
        return self._get_token_details("authorize", code)

    def refresh_token(self, refresh_token):
        return self._get_token_details("refresh", refresh_token)

    def make_request(self, method, url, **kwargs):
        options = {
            "GET": requests.get,
            "POST": requests.post,
            "PUT": requests.put,
            "DELETE": requests.delete,
        }
        if method in ["POST", "PUT"]:
            headers = kwargs.get("headers")
            if headers.get("Content-Type") == "application/json":
                json = kwargs.pop("data", None)
                kwargs.update(json=json)
        return options[method](url, **kwargs)

    def call_api(self, method, path, **kwargs):
        token, realmId = self.fetch_token_from_db()
        url = "{}/v3/company/{}/{}".format(self.base_url, realmId, path)
        headers = kwargs.pop(
            "headers",
            {"Accept": "application/json", "Content-Type": "application/json"},
        )
        params = kwargs.pop("params", {})
        headers.update(Authorization="Bearer {}".format(token))
        return self.make_request(method, url, params=params, headers=headers, **kwargs)

    def get_path(self, path, call=False):
        url = self.base_url
        if call:
            url = self.call_url
        return "{}{}".format(url, path)

    @classmethod
    def get_quickbook_token(cls):
        from .models import QuickbooksStorage

        return QuickbooksStorage.get_token()

    def save_fetched_token(self, result):
        from .models import QuickbooksStorage

        token, status = self.refresh_token(result.refresh_token)
        if status < 400:
            result = QuickbooksStorage.save_token(realmId=result.realmId, **token)
            return result
        raise QuickbooksAPIException(
            "code: {}, description: {}".format(
                token["error"], token["error_description"]
            )
        )

    def fetch_token_from_db(self):
        result = QuickbooksAPI.get_quickbook_token()
        if not result:
            raise QuickbooksAPIException(
                ("Token not available, " "please visit the {} url.").format(
                    self.view_url
                )
            )
        if result.has_expired():
            result = self.save_fetched_token(result)
        return result.access_token, result.realmId

    @property
    def discovery_document(self):
        r = requests.get(settings.DISCOVERY_DOCUMENT)
        if r.status_code >= 400:
            raise QuickbooksAPIException("An error occured")
        discovery_doc_json = r.json()
        return dict(
            issuer=discovery_doc_json["issuer"],
            auth_endpoint=discovery_doc_json["authorization_endpoint"],
            userinfo_endpoint=discovery_doc_json["userinfo_endpoint"],
            revoke_endpoint=discovery_doc_json["revocation_endpoint"],
            token_endpoint=discovery_doc_json["token_endpoint"],
            jwks_uri=discovery_doc_json["jwks_uri"],
        )

    # Api calls
    def create_customer(self, **kwargs):
        # data is sent in the following form
        """

        """
        data = {
            "BillAddr": {
                "Line1": kwargs["location"]["address"],
                "Country": kwargs["location"]["country"],
            },
            "GivenName": kwargs["full_name"],
            "DisplayName": kwargs["email"],
            "PrimaryPhone": {"FreeFormNumber": kwargs["phone_number"]},
            "PrimaryEmailAddr": {"Address": kwargs["email"]},
        }
        response = self.call_api("POST", "customer", data=data)
        if response.status_code >= 400:
            errors = response.json()["Fault"]["Error"]
            error = errors[0]
            if (
                error["Message"] == "Duplicate Name Exists Error"
                or error["code"] == "6240"
            ):
                return self.get_customer_by_email(kwargs["email"])
            print(response.text)
            logger.error("Failed to create new user", exec_info=True)
            response.raise_for_status()
        result = response.json()["Customer"]
        return {"id": result["Id"], "name": result["DisplayName"]}

    def get_customer_by_email(self, email):
        query = "select * from Customer Where DisplayName = '{}'".format(email)
        response = self.call_api("GET", "query", params={"query": query})
        if response.status_code >= 400:
            print(response.text)
            logger.error("Failed to find user by email", exec_info=True)

            response.raise_for_status()
        result = response.json()["QueryResponse"]["Customer"]
        if len(result) > 0:
            record = result[0]
            return {"id": record["Id"], "name": record["DisplayName"]}
        return None

    def create_sales_receipt(self, customer, item):
        data = {
            # "Id": item['id'],
            "CustomerRef": {"value": customer["id"], "name": customer["name"]},
            "CurrencyRef": {"value": item["currency"]},
            "Line": [
                {
                    "Id": "1",
                    "LineNum": 1,
                    "Description": item["description"],
                    "Amount": item["price"],
                    "DetailType": "SalesItemLineDetail",
                    "SalesItemLineDetail": {
                        "UnitPrice": item["amount"],
                        "Qty": 1,
                        "DiscountAmt": item["discount"],
                    },
                }
            ],
        }
        response = self.call_api("POST", "salesreceipt", data=data)
        if response.status_code >= 400:
            logger.error("Failed to create sales receipt", exec_info=True)
            response.raise_for_status()
        result = response.json()["SalesReceipt"]
        return result["Id"]

    def get_sales_receipt(self, order):
        return self.call_api(
            "GET",
            "salesreceipt/{}/pdf".format(order),
            headers={"content-type": "application/pdf"},
        )


def parse_xml(string):
    value = ElementTree.fromstring(string)
    data = {}
    for child in value[0]:
        rr = child.tag.replace("{http://schema.intuit.com/finance/v3}", "")
        data[rr] = child.text
    return data
