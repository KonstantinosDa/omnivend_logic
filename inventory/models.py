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
    location_name = models.CharField(max_length=200)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    

class VendingMachine(models.Model):
    MachineName = models.CharField(max_length=250, blank=True, editable=False)
    location_name = models.CharField(max_length=200)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
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