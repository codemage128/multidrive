from django.db import models

# Create your models here.
class Setting(models.Model):
     dropbox = models.CharField(max_length=255)
     google_token = models.CharField(max_length=255)
     google_projectid = models.CharField(max_length=255)
     one_tenant = models.CharField(max_length=255)
     one_client = models.CharField(max_length=255)
     one_security = models.CharField(max_length=255)
