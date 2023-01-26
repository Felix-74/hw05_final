from django.db import models


class ChangePasswordAfterReset(models.Model):
    new_pass = models.CharField(max_length=50)
    new_pass_confirm = models.CharField(max_length=50)
