from django.test import TestCase
from quickbooks.models import QuickbooksStorage


class ModelTestCase(TestCase):
    def test_save_token_without_issues(self):
        self.assertEqual(QuickbooksStorage.objects.count(), 0)
        data = {'token_type': 'bearer', 'access_token': 'eyJlbmMiOiJBMTI4Q0JDLUhTMjU2IiwiYWxnIjoiZGlyIn0..X4zMo3CYEH_E5I6Sa26l8g.fbJBBGYi8mXyn85P0wZk1tMXlMDNuUmQKneJBTAw5i5uuusZCOW0nxBJ1vJGNFjLPCE5R6NpRI-OymEnwJNCkSq7_LNMNqscMhxa8kw4AFZ9qRsZfzuVXDbPO9KKafjUymqFO3oUGWuPOi4UFUECWQdyGqBCrFiJAkSvLLimoM8wsAI2mi8o1GYi-rtu4xslzZMHNDChc8X2NKA4WBG0zXK0sPx_M-DI6l-nCKLuNZ15eLg-OQTmqzfvbYqYWkuHgdR1hnwYzqlDSn1k43sv5ZJGPVmD-Ih01D8rlwdsba8sT5UH9dBIeWA5egDKzQGz4RXZB-1CAKa89wMl_e3dGiD_U1D1Pf0pjHJ1TJ9NdTvB7DH7XZLp_lwwJR8HUY36WZALU85dQpkifpDKS9lUun9V2gDDQ8qe8J_wMRmUtXOexrglH_BKLhdt7QGCUR5hWpG7ZltY5lDRKH0FH7002gLKj77OFn91b0k4in_SZgzq82-iqY3bs4KS1vkz9azOxPDI9kZZrDXTtIAgjkF6zqVP0Csx-RjGJcdT3ic7M2Ex7RGUXs77MU0pE_wsMEDpur-o5eKZrnUzF7TXh-cIjtdm4Cs29Yhcua1gCmdevmypbhGOPxHKZkb0Qxn5kh-1aPgOZFXj-43OmoSKCgcxv8RhaNvbGUkOJGiVV8zs7q-mTMnZjyaF3WbR_e-UNv45.0KYfIXz0CXC98Y9RU_X2Jw', 'expires_in': 3600, 'x_refresh_token_expires_in': 8726400, 'refresh_token': 'Q011532409540WRuIrTP6aZQ7b5QVlbdO6UNYutau5xhdJZJud'}
        result = QuickbooksStorage.save_token("2329382323", **data)
        self.assertEqual(QuickbooksStorage.objects.count(), 1)
        self.assertEqual(result.access_token, data['access_token'])
        self.assertEqual(result.refresh_token, data['refresh_token'])
