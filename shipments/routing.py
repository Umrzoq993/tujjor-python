# shipments/routing.py
from django.urls import re_path
from .consumers import ShipmentConsumer

websocket_urlpatterns = [
    re_path(r"ws/shipments/$", ShipmentConsumer.as_asgi()),
]
