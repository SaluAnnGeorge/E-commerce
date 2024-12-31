from django.contrib import messages
from django.contrib.auth.models import User
import re
from django.shortcuts import redirect, render
from django.contrib.auth.hashers import make_password
from .models import Customer,Product,Cart
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

def index(request):
    products = Product.objects.all()  
    paginator = Paginator(products, 3)  # Show 3 movies per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'index.html', {'page_obj': page_obj}) 

def product_detail(request, product_id):
    # Fetch the product with the given ID or return a 404 error if not found
    product = get_object_or_404(Product, id=product_id)
    # Pass the product to the template
    return render(request, 'product_detail.html', {'product': product})


def register(request):
    if request.method == "POST":
        customer_name = request.POST.get("customer_name")
        contact_number = request.POST.get("contact_number")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        print("Received POST request")  # Debugging line

        # Validate contact number
        if not re.fullmatch(r"^\d{10}$", contact_number):
            messages.error(request, "Contact number must be exactly 10 digits.")
            return redirect("register")

        # Validate password (ensure at least 1 uppercase letter and 1 special character)
        if not re.fullmatch(r"^(?=.*[A-Z])(?=.*[@$!%?&])[A-Za-z\d@$!%?&]{8,}$", password):
            messages.error(request, "Password must be at least 8 characters long, include 1 uppercase letter, and 1 special character.")
            return redirect("register")

        # Confirm passwords match
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("register")

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered!")
            return redirect("register")

        # Create the user
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password  # Django automatically hashes it
        )
        print("User created")  # Debugging line

        # Create the associated Customer instance
        Customer.objects.create(
            user=user,
            customer_name=customer_name,
            contact_number=contact_number,
            email=email,
            password=make_password(password)  # Optional; Django already hashes the password
        )
        print("Customer instance created")  # Debugging line

        # Success message and redirect to login
        messages.success(request, "Registration successful! You can now log in.")
        return redirect("login")

    return render(request, "register.html")


from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout

def login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        

        # Use Django's authenticate function
        user = authenticate(request, username=email, password=password)

        if user is not None:
            # Log the user in
            auth_login(request, user)
            messages.success(request, "You are now logged in.")
            return redirect("index")
        else:
            messages.error(request, "Invalid email or password.")
            return redirect("login")

    return render(request, "login.html")


# Logout View
def logout(request):
    auth_logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("index")
from django.shortcuts import render
from .models import Product, Category

def product_list(request):
    category_id = request.GET.get("category", None)  # Get selected category ID from the dropdown
    categories = Category.objects.all()  # Fetch all categories

    if category_id:  # Filter products if a category is selected
        products = Product.objects.filter(category_id=category_id)
    else:  # Show all products if no category is selected
        products = Product.objects.all()

    return render(request, "search_results.html", {
        "categories": categories,
        "products": products,
        "selected_category": category_id,  # Pass selected category to template
    })

from django.shortcuts import render
from .models import Product

def product_search(request):
    search_query = request.GET.get('search', '').strip()  # Strip to avoid leading/trailing spaces

    # Ensure we're not using None as a filter value
    if search_query:
        products = Product.objects.filter(name__icontains=search_query)
    else:
        products = Product.objects.all()  # Display all products if no search term

    return render(request, 'search_results.html', {'products': products})



@login_required
def cart(request):
    customer = request.user.customer
    cart_items = Cart.objects.filter(customer=customer)
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
    }
    return render(request, 'cart.html', context)


from django.shortcuts import get_object_or_404

@login_required(login_url='login')  # Ensure the user is logged in
def add_to_cart(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))  # Default quantity to 1 if not provided

        # Fetch the product or return a 404 if it doesn't exist
        product = get_object_or_404(Product, id=product_id)

        if product.stock >= quantity:  # Check if enough stock is available
            customer = request.user.customer  # Get the logged-in customer's object
            cart_item, created = Cart.objects.get_or_create(
                customer=customer, product=product,
                defaults={'quantity': quantity}
            )
            if not created:  # If the item already exists in the cart
                cart_item.quantity += quantity  # Increment the quantity
                if cart_item.quantity > product.stock:  # Ensure it doesn't exceed available stock
                    cart_item.quantity = product.stock
                cart_item.save()

            messages.success(request, f"Added {quantity} '{product.name}' to your cart.")
        else:
            messages.error(request, f"Sorry, only {product.stock} '{product.name}' available in stock.")

    return redirect('cart')

from django.shortcuts import redirect
from .models import Cart, Product

def increase_quantity(request, product_id):
    # Logic for increasing the quantity of the product in the cart
    try:
        cart_item = Cart.objects.get(product_id=product_id, user=request.user)
        cart_item.quantity += 1  # Increment the quantity
        cart_item.save()
    except Cart.DoesNotExist:
        # Handle the case where the cart item doesn't exist
        pass

    return redirect('cart')  # Redirect back to the cart page

@login_required
def increase_quantity(request, cart_item_id):
    cart_item = Cart.objects.get(pk=cart_item_id)

    # Use the correct field name 'stock' instead of 'quantity_in_stock'
    if cart_item.quantity < cart_item.product.stock:
        cart_item.quantity += 1
        cart_item.save()
    else:
        messages.error(request, f"Cannot add more of '{cart_item.product.name}' to the cart. Only {cart_item.product.stock} available in stock.")

    return redirect('cart')


@login_required
def decrease_quantity(request, cart_item_id):
    cart_item = Cart.objects.get(pk=cart_item_id)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()
    return redirect('cart')


@login_required
def delete_item_in_cart(request, id):
    customer = request.user.customer
    product = get_object_or_404(Product, id=id)
    cart_item = Cart.objects.get(customer=customer, product=product)
    cart_item.delete()
    return redirect('cart')

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product, Wishlist

@login_required(login_url='login')
def wishlist(request):
    user = request.user
    wishlist = Wishlist.objects.filter(user=user)
    return render(request, 'wishlist.html', {'wishlist': wishlist})

@login_required(login_url='login')
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    return redirect('wishlist')

def remove_from_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Wishlist.objects.filter(user=request.user, product=product).delete()
    return redirect('wishlist')