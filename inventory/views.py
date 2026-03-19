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


def edit_store(request):
    DAY_BITMASK = {
        "Mon": 1,    
        "Tue": 2,    
        "Wed": 4,    
        "Thu": 8,    
        "Fri": 16,   
        "Sat": 32,   
        "Sun": 64    
    }

    if request.method == "POST":
        store_id = request.POST.get("store_id")
        store = get_object_or_404(Store, id=store_id)
        action = request.POST.get("action")

        if action =='save':
            selected_days = request.POST.getlist("open_days")
            open_days = sum(DAY_BITMASK[day] for day in selected_days)
            store.location_name = request.POST.get("location_name")
            store.status = request.POST.get("status")
            store.latitude = request.POST.get("latitude")
            store.longitude = request.POST.get("longitude")
            store.opening_time = request.POST.get("opening_time")
            store.closing_time = request.POST.get("closing_time")   
            store.open_days = open_days     
            store.save()

        elif action == "delete":
            store.delete()

    return redirect('dashboard')


def edit_machine(request):
    print('-----------------__________________---------------------')
    if request.method == "POST":
        machine_id = request.POST.get("machine_id")
        machine = get_object_or_404(VendingMachine, id=machine_id)
        action = request.POST.get("action")

        if action == "save":
            machine.location_name = request.POST.get("location_name")
            machine.latitude = request.POST.get("latitude")
            machine.longitude = request.POST.get("longitude")
            print(request.POST.get("status"))
            print(machine.status)
            machine.status = request.POST.get("status")
            print(machine.status)
            machine.save()

        #-_- add the functionality to add prodacts to the machine and to what slot 



        elif action =='delete':
            machine.delete()
            
    return redirect('dashboard')
 