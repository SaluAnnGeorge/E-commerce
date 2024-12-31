    
from django.contrib.auth.models import User
from django.db import models

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)

    def __str__(self):
        return self.customer_name

# Create your models here.
class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.FloatField()
    stock = models.IntegerField()
    category = models.ForeignKey("Category", on_delete=models.CASCADE, default=1) 
    image = models.ImageField(upload_to='product_images/')
    description = models.TextField()
    product_type = models.CharField(max_length=255, null=True, blank=True)
    country_of_origin = models.CharField(max_length=255, null=True, blank=True)
    
  

    def __str__(self):
        return self.name
    



from django.db import models 


class Category(models.Model): 
	name = models.CharField(max_length=50) 

	@staticmethod
	def get_all_categories(): 
		return Category.objects.all() 

	def __str__(self): 
		return self.name 

class Cart(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)

    def sub_total(self):
        return int(self.product.price) * int(self.quantity)

    def __str__(self):
        return f"Cart - Customer: {self.customer.customer_name} - Product: {self.product.product_name} - Qty: {self.quantity}"



class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username}'s Wishlist - {self.product.name}"