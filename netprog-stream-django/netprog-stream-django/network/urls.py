from django.contrib import admin
from django.urls import path

from . import views

urlpatterns = [
    path('', views.index),
    path('device/<int:device_id>', views.get_device_stats, name="device"),
    # path('devices', views.get_devices),
]
