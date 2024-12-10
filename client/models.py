from django.db import models
from django.contrib.auth.models import AbstractUser

class Client(models.Model):
    name = models.CharField(max_length=250, blank=True, null=True)
    email = models.EmailField(blank=True, null = True)
    
    class Meta:
        verbose_name_plural = "Clients"
    
    def __str__(self):
        return self.name

class ClientUser(AbstractUser):
    # Additional fields specific to Client can be added here if needed
    # Example
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="ClientUsers", null=True, blank=True)
    
    def __str__(self):
        return f'{self.client}-{self.username}'


class Engagement(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="engagements")
    engagement_id = models.IntegerField()
    engagement_title = models.CharField(max_length=200)

    ENGAGEMENT_TYPES = [
        ('classification', 'Classification'),
        ('regression', 'Regression'),
    ]

    engagement_type = models.CharField(
        max_length=15, 
        choices=ENGAGEMENT_TYPES, 
        default='classification'
    )
    
    def __str__(self):
        return f"{self.client} - {self.engagement_title}"