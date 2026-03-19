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
    # Link to the Category model
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, # If category is deleted, keep product but set category to null
        null=True,
        related_name='products'
    )
    price = models.DecimalField(max_digits=6, decimal_places=2)
    stock_quantity = models.IntegerField(default=0) # Good for vending inventory
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    def __str__(self):
        return f"{self.name} ({self.category.name if self.category else 'No Category'})"






class MachineStock(models.Model):
    vending_machine = models.ForeignKey(VendingMachine, on_delete=models.CASCADE, related_name='inventory')
    vending_machine_slot = models.CharField(max_length=4)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        # Prevents having two separate rows for the same product in the same machine
        unique_together = ('vending_machine', 'vending_machine_slot')

    def __str__(self):
        return f"{self.quantity}x {self.product.name} at {self.vending_machine.MachineName}"