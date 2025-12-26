from django.db import models 
from pgvector.django import VectorField


class Shop(models.Model): 
    name = models.CharField(max_length=255) 
    category = models.CharField(max_length=255) 
    latitude = models.FloatField() 
    longitude = models.FloatField() 
    embedding = VectorField(dimensions=384) 

    def __str__(self): 
        return self.name