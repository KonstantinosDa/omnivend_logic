from django.shortcuts import render, redirect, get_object_or_404
from .models import Product
from rest_framework import generics
from .models import VendingMachine
from .serializers import VendingMachineSerializer
from .forms import MachineForm, ProductForm
from django.contrib.auth.decorators import login_required

class VendingMachineList(generics.ListCreateAPIView):
    queryset = VendingMachine.objects.all()
    serializer_class = VendingMachineSerializer


def landing_page(request):
    products = Product.objects.all() # Fetch all products from DB
    return render(request, 'inventory/landing.html', {'products': products})

@login_required
def dashboard_home(request):
    # Fetch all machines so we can show them in a list
    machines = VendingMachine.objects.all()
    
    return render(request, 'inventory/dashboard_home.html', {
        'machines': machines,
        'machine_count': machines.count()
    })


