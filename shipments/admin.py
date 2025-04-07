from django.contrib import admin
from .models import Shipment, ShipmentStatusHistory

@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'receiver_name', 'status', 'created_at')
    search_fields = ('receiver_name', 'receiver_phone', 'sender__username')
    list_filter = ('status', 'created_at')

@admin.register(ShipmentStatusHistory)
class ShipmentStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('shipment', 'old_status', 'new_status', 'changed_at')
    search_fields = ('shipment__id',)
    list_filter = ('old_status', 'new_status', 'changed_at')
