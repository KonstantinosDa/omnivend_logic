from django.contrib import admin

# Register your models here.
from .models import VendingMachine, Product,Category,Store,MachineStock

admin.site.register(VendingMachine)
admin.site.register(Product)
admin.site.register(Category)
admin.site.register(Store)
admin.site.register(MachineStock)