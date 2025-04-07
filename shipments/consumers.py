# shipments/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ShipmentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("shipments_group", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("shipments_group", self.channel_name)

    async def shipment_status_changed(self, event):
        """
        event dict:
        {
          "type": "shipment_status_changed",
          "shipment_id": ...,
          "old_status": ...,
          "new_status": ...
        }
        """
        await self.send(json.dumps(event))
