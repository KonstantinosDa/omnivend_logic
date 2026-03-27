from rest_framework import serializers
from .models import VendingMachine, MachineStock

class MachineStockSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    slot = serializers.IntegerField(source='vending_machine_slot')

    class Meta:
        model = MachineStock
        fields = ['slot', 'product_name', 'quantity']

class VendingMachineSerializer(serializers.ModelSerializer):
    inventory = MachineStockSerializer(many=True, read_only=True)

    class Meta:
        model = VendingMachine
        fields = ['id', 'location_name', 'inventory']