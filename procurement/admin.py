from django.contrib import admin
from .models import ProcurementOrder, ProcurementOrderItem

@admin.register(ProcurementOrder)
class ProcurementOrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'supplier', 'total_cost', 'is_delivered']
    list_filter = ['is_delivered', 'supplier']

@admin.register(ProcurementOrderItem)
class ProcurementOrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'component', 'quantity_ordered', 'quantity_delivered', 'unit_price']
