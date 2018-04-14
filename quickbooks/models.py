from django.db import models
from django.contrib.postgres.fields import JSONField
from django.utils import timezone
import json

# Create your models here.
"""
{ 
"token_type": "bearer", 
"expires_in": 3600, 
"refresh_token":"L311478109728uVoOkDSUCl4s8FDRvjHR6kUKz0RHe3WtZQuBq",
"x_refresh_token_expires_in":15552000,
"access_token":"eyJlbmMiOiJBMTI4Q0JDLUhTMjU2IiwiYWxnIjoiZGlyIn0..KM1_Fezsm6BUSaqqfTedaA.
dBUCZWiVmjH8CdpXeh_pmaM3kJlJkLEqJlfmavwGQDThcf94fbj9nBZkjEPLvBcQznJnEmltCIvsTGX0ue_w45h7_
yn1zBoOb-1QIYVE0E5TI9z4tMUgQNeUkD1w-X8ECVraeOEecKaqSW32Oae0yfKhDFbwQZnptbPzIDaqiduiM_q
EFcbAzT-7-znVd09lE3BTpdMF9MYqWdI5wPqbP8okMI0l8aa-UVFDH9wtli80zhHb7GgI1eudqRQc0sS9zWWb
I-eRcIhjcIndNUowSFCrVcYG6_kIj3uRUmIV-KjJUeXdSV9kcTAWL9UGYoMnTPQemStBd2thevPUuvKrPdz3ED
ft-RVRLQYUJSJ1oA2Q213Uv4kFQJgNinYuG9co_qAE6A2YzVn6A8jCap6qGR6vWHFoLjM2TutVd6eOeYoL2bb7jl
QALEpYGj4E1h3y2xZITWvnmI0CEL_dYQX6B3QTO36TDaVl9WnTaCCgAcP6bt70rFlPYbCjOxLoI6qFm5pUwGLLp
67JZ36grc58k7NIyKJ8dLJUL_Q9r1WoUvw.ZS298t_u7dSlkfajxLfO9Q"
}"""


class QuickbooksStorage(models.Model):
    token = models.TextField()
    realmId = models.CharField(max_length=200, null=True)
    date_added = models.DateTimeField(auto_now_add=True)

    @property
    def raw_token(self):
        return json.loads(self.token)

    @property
    def access_token(self):
        return self.raw_token['access_token']

    @property
    def refresh_token(self):
        return self.raw_token['refresh_token']

    @classmethod
    def save_token(cls, realmId, **kwargs):
        cls.objects.all().delete()
        return cls.objects.create(token=json.dumps(kwargs), realmId=realmId)

    def has_expired(self, kind='access_token'):
        options = {
            'access_token': 1,
            'refresh_token': 100*24
        }
        timestamp = timezone.now() - self.date_added
        in_hours = timestamp.total_seconds() / 3600
        return in_hours > options[kind]

    @classmethod
    def get_token(cls):
        return cls.objects.first()
