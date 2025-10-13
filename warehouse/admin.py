from django.contrib import admin
from .models import Warehouse, ComponentStock, BikeStock, WarehouseType

admin.site.register(Warehouse)
admin.site.register(ComponentStock)
admin.site.register(BikeStock)
admin.site.register(WarehouseType)
