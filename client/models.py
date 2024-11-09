from django.db import models
from django.contrib.auth.models import AbstractUser

class Client(AbstractUser):
    # Additional fields specific to Client can be added here if needed
    # Example: 
    organization = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return self.username

class Engagement(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="engagements")
    engagement_title = models.CharField(max_length=200)
    
    def __str__(self):
        return f"{self.client.username} - {self.engagement_title}"