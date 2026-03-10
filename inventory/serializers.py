from rest_framework import serializers
from .models import VendingMachine, MachineStock

class MachineStockSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')

    class Meta:
        model = MachineStock
        fields = ['vending_machine_slot', 'product_name', 'quantity']

class VendingMachineSerializer(serializers.ModelSerializer):
    # This shows the snacks inside the machine when you look at the machine
    inventory = MachineStockSerializer(many=True, read_only=True)

    class Meta:
        model = VendingMachine
        fields = ['id', 'location_name', 'latitude', 'longitude', 'inventory']