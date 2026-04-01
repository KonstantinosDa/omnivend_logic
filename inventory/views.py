from django.shortcuts import render, redirect, get_object_or_404
from .models import Product
from rest_framework import generics
from .models import VendingMachine,Store,Storage,Product,Category,Sales,MachineStock,OrderItem,Order,Item_Sales
from .serializers import VendingMachineSerializer
from .forms import MachineForm, ProductForm
from django.contrib.auth.decorators import login_required
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.utils.timezone import now
import requests

today = now().date()
class VendingMachineList(generics.ListCreateAPIView):

    queryset = VendingMachine.objects.all()
    serializer_class = VendingMachineSerializer

def weather_code(code):
    if code == 0:
        return "sunny"

    elif code in [1, 2, 3]:
        return "partly_cloudy"
    
    elif code in [61, 63, 65]:
        return "rainy"
    
    else:
        return "cloudy"

@api_view(['POST'])
def sync_machine_stock(request):
    machine_id = request.data.get("machine_id")
    stock_data = request.data.get("stock", [])
    try:
        machine = VendingMachine.objects.get(id=machine_id)
        stock_items = machine.inventory.all()
        
    except VendingMachine.DoesNotExist:
        return Response({"error": "Machine not found"}, status=404)
    if request.data.get("event") == "sync":
        new_order, created = Order.objects.get_or_create(
                order_type = "restock",
                machine = machine,
                status="pending"

            )

        for item in stock_data:
            url = "https://api.open-meteo.com/v1/forecast?latitude={machine.latitude}.98&longitude={machine.longitude}.81&current_weather=true"
            response = requests.get(url)
            data = response.json()
            temp = data["current_weather"]["temperature"]
            code = data["current_weather"]["weathercode"]
            weather = weather_code(code)

            product = Product.objects.get(id=item["product_id"])
            stock_item = stock_items.get(vending_machine_slot=item["slot"])
            stock_item.quantity =item["quantity"]
            
            sale, created = Sales.objects.get_or_create(
                machine=machine,                 
                interval_type="day",
                created_at=today,
                defaults={
                    "source_type": "machine",
                    "amount": 0
                }
            )
            item_sale, created_ =Item_Sales.objects.get(
                machine_item=item,                 
                interval_type="day",
                created_at=today,
                defaults={
                    "source_type": "machine",
                    "amount": 0
                }
            )

            if not item_sale.temperature_weather:
                item_sale.temperature_weather = temp

            if not item_sale.weather_type:    
                item_sale.weather_type = weather

            item_sale.amount += item["sold"] * product.price
            sale.amount += item["sold"] * product.price
            stock_item.sold_this_wheek = item["sold"]
            sale.save()
            stock_item.save()
            machine.save()
            stock_item.save()

            if stock_item.quantity < stock_item.restock_threshold:
                order_item, created = OrderItem.objects.get_or_create(
                    order=new_order,
                    product=product,
                    slot=item["slot"],
                    defaults={
                        "quantity": min(
                            stock_item.expected_demand,
                            machine.slot_cap - item["quantity"]
                        )
                    }
                )

                if not created:
                    #  update quantity instead of duplicating
                    order_item.quantity = min(
                        stock_item.expected_demand,
                        machine.slot_cap - item["quantity"]
                    )
                    order_item.save()

        if not new_order.items.exists():
            new_order.delete()
            
    return Response({"status": "stock synced"})


def landing_page(request):

    products = Product.objects.all() 
    return render(request, 'inventory/landing.html', {'products': products})


@login_required
def dashboard_home(request):

    machines = VendingMachine.objects.all()
    stores = Store.objects.all()
    storage = Storage.objects.all()
    products = Product.objects.all()
    category = Category.objects.all()
    return render(request, 'inventory/dashboard_home.html', {
        'stores' : stores,
        'store_count' : stores.count(),
        'machines': machines,
        'machine_count': machines.count(),
        'storage' : storage,
        'storage_count' : storage.count(),
        'products' : products,
        'product_count' : products.count(),
        'category': category,
        'category_count': category.count(),

    })


def add_machine(request):

    if request.method == "POST":
        VendingMachine.objects.create(
            MachineName=request.POST['machine_name'],
            location_name=request.POST['location_name'],
            latitude=request.POST['latitude'],
            longitude=request.POST['longitude'],
            slot_cap= request.POST['capaciry']
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

    if request.method == "POST":
        machine_id = request.POST.get("machine_id")
        machine = get_object_or_404(VendingMachine, id=machine_id)
        action = request.POST.get("action")

        if action == "save":
            machine.MachineName=  request.POST.get("machineName")
            machine.location_name = request.POST.get("location_name")
            machine.latitude = request.POST.get("latitude")
            machine.longitude = request.POST.get("longitude")
            machine.status = request.POST.get("status")
            machine.save()

        #-_- add the functionality to add prodacts to the machine and to what slot 



        elif action =='delete':
            machine.delete()
            
    return redirect('dashboard')


def add_storage(request):

    if request.method == "POST":
        Storage.objects.create(
            name=request.POST['name'],
            location_name=request.POST['location_name'],
            latitude=float(request.POST['latitude']),
            longitude=float(request.POST['longitude']),
        )
    return redirect('dashboard')


def edit_storage(request):

    if request.method == "POST":
        storage_id = request.POST.get("storage_id")
        storage = get_object_or_404(Storage, id=storage_id)
        action = request.POST.get("action")

        if action == "save":
            storage.name = request.POST.get("location_name")
            storage.location_name = request.POST.get("location_name")
            storage.latitude = request.POST.get("latitude")
            storage.longitude = request.POST.get("longitude")
            storage.save()

        elif action =='delete':
            storage.delete()
            
    return redirect('dashboard')

def add_product(request):
    if request.method == "POST":
        category_id = request.POST.get("category")
        category = Category.objects.get(id=category_id)
        image_ = request.FILES.get("image")
        print(request.FILES)
        Product.objects.create(
            name=request.POST['name'],
            category=category,
            price=float(request.POST['Price']),
            stock_quantity=float(request.POST['stock_quantity']),
            image=image_,
        )
    return redirect('dashboard')

def edit_product(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        product = get_object_or_404(Product, id=product_id)
        action = request.POST.get("action")
        category_id = request.POST.get("category")
        category = Category.objects.get(id=category_id)
        print(request.POST.get("category"))
        if action == "save":
            product.name = request.POST.get("name")
            product.price = request.POST.get("price")
            product.stock_quantity = request.POST.get("stock_quantity")
            product.image = request.FILES.get("image")
            product.category =category
            product.save()

        elif action =='delete':
            product.delete()
            
    return redirect('dashboard')




