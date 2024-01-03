from django.db import models
from django.contrib.auth.models import User

import uuid 

# Справочник операций
class OperationType(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    name = models.CharField(max_length=128)
    exec_time = models.TimeField(auto_now=False, auto_now_add=False)
