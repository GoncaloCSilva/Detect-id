from django.db import models

# Create your models here.
class Utente(models.Model):
    firstname = models.CharField(max_length=255)
    lastname = models.CharField(max_length=255)
    gender = models.CharField(max_length=255)
    risk = models.CharField(max_length=255)
    birthday = models.DateField()

    def __str__(self):
        return f"{self.firstname} {self.lastname}"