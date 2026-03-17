from django.shortcuts import render, redirect, get_object_or_404
from .models import Product
from rest_framework import generics
from .models import VendingMachine,Store
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
    stores = Store.objects.all()
    
    return render(request, 'inventory/dashboard_home.html', {
        'stores' : stores,
        'store_count' : stores.count(),
        'machines': machines,
        'machine_count': machines.count()
    })


def add_machine(request):
    if request.method == "POST":
        VendingMachine.objects.create(
            location_name=request.POST['location_name'],
            latitude=request.POST['latitude'],
            longitude=request.POST['longitude'],
        )
    return redirect('dashboard')

def add_store(request):
    if request.method == "POST":
        selected_days = request.POST.getlist('open_days')

        # Convert strings → int and sum them 
        open_days_int = sum(int(day) for day in selected_days)
        Store.objects.create(
            location_name=request.POST['location_name'],
            latitude=float(request.POST['latitude']),
            longitude=float(request.POST['longitude']),
            open_days = open_days_int,
            opening_time = request.POST['opening_time'],
            closing_time = request.POST['closing_time'],
        )
    return redirect('dashboard')
