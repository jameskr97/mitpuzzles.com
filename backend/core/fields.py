from django.db import models

class ULIDField(models.Field):
    def db_type(self, connection):
        return 'ulid'