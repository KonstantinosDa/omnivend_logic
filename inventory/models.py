from django.db import models
from django.utils.text import slugify



class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True) 

    def save(self, *args, **kwargs):
        # Only generate a slug if one doesn't exist yet
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name
    
class Storage(models.Model):
    name = models.CharField(max_length=100,null=True, blank=True)
    location_name = models.CharField(max_length=200)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)



class Store(models.Model):

    STATUS_CHOICES = {
        ('open', 'Open'),
        ('closed', 'Closed')
    }

    location_name = models.CharField(max_length=200)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Closed')
    opening_time = models.TimeField(null=True, blank=True)
    closing_time = models.TimeField(null=True, blank=True)

    # why IntegerField you ask whelp this is the most efficient way to store this data 
    # every day i going to have a bit value Mon = 1 Tue = 2 Wed = 4 Thu = 8  Fri = 16 Sat = 32 Sun = 64
    # i will save the sum of the days and and when i need to use the dictionary DAY_VALUES to 'decode' the saved value 
    # is it overkill ...yes but i'm trying to land a job and is my idea and i'm proud of it  
    open_days= models.IntegerField(null=True, blank=True)

    def get_open_days_display(self):
        DAY_VALUES = [
            ('Mon', 1),
            ('Tue', 2),
            ('Wed', 4),
            ('Thu', 8),
            ('Fri', 16),
            ('Sat', 32),
            ('Sun', 64),
        ]

        return [day for day, val in DAY_VALUES if self.open_days and (self.open_days & val)]





class VendingMachine(models.Model):

    STATUS_CHOICES = [
        ('active', 'Online'),
        ('inactive', 'Offline'),
        ('maintenance', 'Under Repair'),
    ]


    MachineName = models.CharField(max_length=250, blank=True, editable=False)
    location_name = models.CharField(max_length=200)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='inactive')
    slot_cap = models.IntegerField(default=15)



    def save(self, *args, **kwargs):
        clean_location = self.location_name.replace(" ", "")

        query = VendingMachine.objects.filter(location_name__iexact=self.location_name)

        
        # exclude it from the count so it doesn't count itself
        if self.pk:
            query = query.exclude(pk=self.pk)

        existing_count = query.count()
        
        # Generates the name (e.g., "Airport0")
        self.MachineName = f"{clean_location}_{existing_count}"   
        super().save(*args, **kwargs)

    def __str__(self):
        return self.MachineName





class Product(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='products'
    )
    price = models.DecimalField(max_digits=6, decimal_places=2)
    stock_quantity = models.IntegerField(default=0)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    def __str__(self):
        return f"{self.name} ({self.category.name if self.category else 'No Category'})"



class StorageStock(models.Model):
    storage = models.ForeignKey(Storage, on_delete=models.CASCADE, related_name='inventory')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)

class MachineStock(models.Model):
    DEMAND_CHOICES = [
        ("auto","Auto"),
        ("set","Set")
    ]
    demadn_setting = models.CharField(max_length=20, choices=DEMAND_CHOICES,default="auto")
    vending_machine = models.ForeignKey(VendingMachine, on_delete=models.CASCADE, related_name='inventory')
    vending_machine_slot = models.CharField(max_length=4)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    expected_demand = models.PositiveIntegerField(blank=True, null=True)
    restock_threshold = models.PositiveIntegerField(blank=True, null=True)
    sold_this_month= models.PositiveIntegerField(blank=True, null=True,default=0)
    
    def save(self, *args, **kwargs):
        if not self.expected_demand:
            self.expected_demand = self.vending_machine.slot_cap

        if not self.restock_threshold:
            self.restock_threshold = self.vending_machine.slot_cap
        super().save(*args, **kwargs)
    
    class Meta:
        # Prevents having two separate rows for the same product in the same machine
        unique_together = ('vending_machine', 'vending_machine_slot')

    def __str__(self):
        return f"{self.quantity}x {self.product.name} at {self.vending_machine.MachineName}"

class Order(models.Model):
    ORDER_TYPE_CHOICES = [
        ("store", "Store Order"),
        ("restock", "Restock Order"),
    ]
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[("pending", "Pending"),("in_transit","in transit") ,("completed", "Completed")],
        default="pending"
    )
    
    store = models.ForeignKey(Store, null=True, blank=True, on_delete=models.CASCADE, related_name='order')
    machine = models.ForeignKey(VendingMachine, null=True, blank=True, on_delete=models.CASCADE, related_name='order')

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    slot = models.CharField(max_length=4,null=True, blank=True)  # only used for machine orders
    quantity = models.IntegerField()

class Sales(models.Model):
    SOURCE = [
        ("store", "Store"),
        ("machine", "Machine"),
    ]

    INTERVALS = [
        ("day", "day"),
        ("week", "week"),
        ("month", "month"),
        ("year", "year"),
    ]

    source_type = models.CharField(max_length=20, choices=SOURCE)
    machine = models.ForeignKey(VendingMachine, null=True, blank=True, on_delete=models.CASCADE, related_name='sales')
    store = models.ForeignKey(Store, null=True, blank=True, on_delete=models.CASCADE, related_name='sales')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    interval_type = models.CharField(max_length=20, choices=INTERVALS)
    created_at  = models.DateField()
    ended_at = models.DateField(null=True, blank=True)
  
    class Meta:
        unique_together = ("machine", "interval_type", "created_at")

    def clean(self):

        super().clean()
        if self.source_type == "machine" and not self.machine:
            raise ValidationError("Machine must be set when source_type is 'machine'.")
        if self.source_type == "store" and not self.store:
            raise ValidationError("Store must be set when source_type is 'store'.")
        if self.source_type == "machine" and self.store:
            raise ValidationError("Store must be empty when source_type is 'machine'.")
        if self.source_type == "store" and self.machine:
            raise ValidationError("Machine must be empty when source_type is 'store'.")

class Item_Sales(models.Model):
    SOURCE = [
        ("store", "Store"),
        ("machine", "Machine"),
    ]

    INTERVALS = [
        ("day", "day"),
        ("week", "week"),
        ("month", "month"),
        ("year", "year"),
    ]
    WEATHER_TYPES = [
        ("cloudy","cloudy"),
        ("sunny","sunny"),
        ("windy","windy"),
        ("stormy","stormy"),
        ("partly_cloudy","partly_cloudy"),
        ("rainy","rainy"),
        ("snowy","snowy")
    ]

    source_type = models.CharField(max_length=20, choices=SOURCE)
    machine_item = models.ForeignKey(MachineStock, null=True, blank=True, on_delete=models.CASCADE, related_name='item_sales')
    store_item = models.ForeignKey(StorageStock, null=True, blank=True, on_delete=models.CASCADE, related_name='item_sales')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    interval_type = models.CharField(max_length=20, choices=INTERVALS)
    created_at  = models.DateField()
    ended_at = models.DateField(null=True, blank=True)
    temperature_weather = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2)
    weather_type = models.CharField(null=True, blank=True,max_length=20, choices=WEATHER_TYPES)

