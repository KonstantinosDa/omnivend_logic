from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.db.models import Q
from django.http import HttpResponseForbidden
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import generics
from .models import VendingMachine,Store,Storage,Product,Category,Sales,MachineStock,OrderItem,Order,Item_Sales
from .serializers import VendingMachineSerializer
import requests

ROLE_HIERARCHY = {
    "admin": ["admin", "manager", "driver", "employee", "warehouse"],
    "manager": ["driver", "employee", "warehouse"],
}

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

                if stock_item.demadn_setting == "auto":
                    quantity = min(
                        stock_item.expected_demand,
                        machine.slot_cap - item["quantity"]
                    )
                else:
                    quantity = stock_item.restock_set

                order_item, created = OrderItem.objects.update_or_create(
                    order=new_order,
                    product=product,
                    slot=item["slot"],
                    defaults={
                        "quantity": quantity
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
    
    user = request.user
    if not user.groups.filter(name="admin").exists():
        machines = VendingMachine.objects.filter(
        Q(managers=request.user) | Q(employees=request.user)
    )
        stores = Store.objects.filter(
        Q(managers=request.user) | Q(employees=request.user)
    )
        storage = Storage.objects.filter(
        Q(managers=request.user) | Q(employees=request.user)
    )
        
    else:
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
        'user':user,

    })


def add_machine(request):

    if not request.user.groups.filter(name="admin").exists():
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

    user = request.user
    if not user.groups.filter(name="admin").exists():
        return HttpResponseForbidden("Admins only")
    
    if request.method == "POST":
        selected_days = request.POST.getlist('open_days')

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

def add_storage(request):

    if not request.user.groups.filter(name="admin").exists():
        return HttpResponseForbidden("Admins only")
    
    if request.method == "POST":
        Storage.objects.create(
            name=request.POST['name'],
            location_name=request.POST['location_name'],
            latitude=float(request.POST['latitude']),
            longitude=float(request.POST['longitude']),
        )
    return redirect('dashboard')


def add_product(request):
    
    if not request.user.groups.filter(name="admin").exists():
        return HttpResponseForbidden("Admins only")
    
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


def edit_store(request):
    user = request.user
    if not user.groups.filter(name__in=["manager", "admin"]).exists():
        return HttpResponseForbidden("Admins or Managers only")
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

        if not user.groups.filter(name="admin").exists():
            if not store.managers.filter(id=user.id).exists():
                return HttpResponseForbidden("Not allowed")
            
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
    user = request.user
    if not user.groups.filter(name__in=["manager", "admin"]).exists():
        return HttpResponseForbidden("Admins or Managers only")
    
    if request.method == "POST":
        machine_id = request.POST.get("machine_id")
        machine = get_object_or_404(Store, id=machine_id)

        if not user.groups.filter(name="admin").exists() and not machine.managers.filter(id=user.id).exists():
            return HttpResponseForbidden("Not allowed")
            
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


def edit_machine_inventory(request):
    user = request.user
    if not user.groups.filter(name__in=["manager", "admin"]).exists():
        return HttpResponseForbidden("Admins or Managers only")
    
    if request.method == "POST":
        machine_id =request.POST.get("machine_id")
        machine = get_object_or_404(Store, id=machine_id)

        if not user.groups.filter(name="admin").exists() and not machine.managers.filter(id=user.id).exists():
            return HttpResponseForbidden("Not allowed")
        
        stock_ids = request.POST.getlist("stock_ids[]")
        new_entrys = request.POST.getlist("new_slot_"+str(machine_id))

        for stock_id in stock_ids:
            changed = request.POST.get("changed_"+stock_id)
            if changed != '0' :
                machine_stock = get_object_or_404(MachineStock, id=stock_id)
                machine_stock.demadn_setting= request.POST.get("mode_"+stock_id)
                machine_stock.vending_machine_slot=request.POST.get("slot_"+stock_id)
                machine_stock.product=get_object_or_404(Product,id=request.POST.get("product_"+stock_id))
                machine_stock.quantity=request.POST.get("quantity_"+stock_id)
                machine_stock.restock_threshold=request.POST.get("threshold_"+stock_id)
                machine_stock.save()
                
        for new_entry in new_entrys: 
            MachineStock.objects.create(
                vending_machine= get_object_or_404(VendingMachine,id=machine_id),
                demadn_setting=request.POST.get("new_mode_"+machine_id),
                vending_machine_slot =new_entry,
                product=get_object_or_404(Product,id=request.POST.get("new_product_"+machine_id)),
                quantity=request.POST.get("new_quantity_"+machine_id),
                restock_threshold=request.POST.get("new_threshold_"+machine_id)
            )

        delete_ids = request.POST.getlist("delete_stock_ids")
        for delete_id in delete_ids:
            id_=int(delete_id)
            MachineStock.objects.filter(id=int(id_)).delete()

        return redirect('dashboard')


def edit_storage(request):

    user = request.user
    if not user.groups.filter(name__in=["manager", "admin"]).exists():
        return HttpResponseForbidden("Admins or Managers only")
    
    if request.method == "POST":
        storage_id = request.POST.get("storage_id")
        storage = get_object_or_404(Storage, id=storage_id)

        if not user.groups.filter(name="admin").exists() and not storage.managers.filter(id=user.id).exists():
            return HttpResponseForbidden("Not allowed")
        
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


def edit_product(request):
    
    if not request.user.groups.filter(name="admin").exists():
        return HttpResponseForbidden("Admins only")
    
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



def can_assign_role(user, role):
    user_role = user.groups.first().name if user.groups.exists() else None
    allowed = ROLE_HIERARCHY.get(user_role, [])
    return role in allowed

def signup(request):
    user = request.user
    if not user.groups.filter(name="admin").exists() and not user.groups.filter(name="manager").exists() :
        return HttpResponseForbidden("Not allowed")
    
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        role = request.POST.get("role")

        if password != confirm_password:
            return render(request, "signup.html", {"error": "Passwords do not match"})

        if User.objects.filter(username=username).exists():
            return render(request, "signup.html", {"error": "Username already exists"})
        
        if not can_assign_role(user, role):
            return HttpResponseForbidden("You cannot assign this role")
        
        new_user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        group = Group.objects.get(name=role)
        new_user.groups.add(group)
        
        
    return render(request, "inventory/signup.html", { 
        'ROLE_PERMISSIONS':ROLE_HIERARCHY[user.groups.first().name],

    })

def user_manager(request):
    pass 
