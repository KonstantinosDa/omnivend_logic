from django import forms
from .models import VendingMachine, Product, MachineStock

class MachineForm(forms.ModelForm):
    class Meta:
        model = VendingMachine
        fields = ['location_name', 'latitude', 'longitude', 'status']

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'price', 'image']

