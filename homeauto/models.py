from django.db import models
from django.utils import timezone

SENSOR_CHOICES = [
    ("temperature", "Temperature Sensor"),
    ("humidity", "Humidity Sensor"),
    ("light", "Light Sensor"),
    ("gas", "Gas Leak Sensor"),
    ("motion", "Motion Sensor"),
]

class SensorLog(models.Model):
    timestamp = models.DateTimeField(default=timezone.now)
    sensor = models.CharField(max_length=20, choices=SENSOR_CHOICES)
    event_type = models.CharField(max_length=50)
    value = models.CharField(max_length=100, blank=True, null=True)
    details = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']

class CloudLog(models.Model):
    timestamp = models.DateTimeField(default=timezone.now)
    event_type = models.CharField(max_length=50)
    sensor = models.CharField(max_length=20, choices=SENSOR_CHOICES, blank=True, null=True)
    value = models.CharField(max_length=100, blank=True, null=True)
    details = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']

class UILog(models.Model):
    timestamp = models.DateTimeField(default=timezone.now)
    event_type = models.CharField(max_length=50)
    details = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']
