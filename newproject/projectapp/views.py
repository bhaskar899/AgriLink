from django.db.models.fields import return_None
from django.shortcuts import render, redirect,get_object_or_404
from django.template.context_processors import request
from django.db.models import Q


from .models import Farmer,Retailer,Product,Order, ChatMessage

# Create your views here.
def master(request):
    return render(request,"master.html")

def home(request):
    return render(request,"home.html")

def about(request):
    return render(request,"about.html")

def contact(request):
    return render(request,"contact.html")

# Farmer views logic

def farmer_register(request):
    return render(request,"farmer_register.html")

def farmer_login(request):
    return render(request,"farmer_login.html")

def farmer_dashboard(request):
    return render(request,"farmer_dashboard.html")

def show_products(request):
    return render(request,"show_products.html")

# retailer views logic

def browse_products(request):
    return render(request,"products.html")

def retailer_dashboard(request):
    return render(request,"retailer_dashboard.html")

def retailer_login(request):
    return render(request,"retailer_login.html")

def retailer_register(request):
    return render(request,"retailer_register.html")

def retailer_products(request):
    return render(request,"retailer_products.html")

def track_order(request):
    return render(request,"track_order.html")

# Farmer registration

def farmer_register(request):
    if request.method == "POST":
        name=request.POST['name']
        email=request.POST['email']
        password=request.POST['password']
        contact=request.POST['contact']
        address=request.POST['address']
        gender=request.POST['gender']

        record=Farmer(name=name,email=email,password=password,contact=contact,address=address,gender=gender)
        record.save()

        return redirect('farmer_login')
    return render(request,"farmer_register.html")


# Farmer Login

def farmer_login(request):
    if request.method == "POST":
        name = request.POST.get('name')
        password = request.POST.get('password')

        # Simple login check (DB me check kar rahe hain)
        try:
            user = Farmer.objects.get(name=name, password=password)
            request.session['name'] = user.name
            request.session['user_type']="farmer"
            return redirect('farmer_dashboard')
        except Farmer.DoesNotExist:
            return render(request, 'farmer_login.html', {'error': 'Invalid credentials'})
    return render(request, "farmer_login.html")



# Retailer Registeretion

def retailer_register(request):
    if request.method == "POST":
        name=request.POST['name']
        email=request.POST['email']
        password=request.POST['password']
        contact=request.POST['contact']
        address=request.POST['address']
        gender=request.POST['gender']

        record=Retailer(name=name,email=email,password=password,contact=contact,address=address,gender=gender)
        record.save()

        return redirect('retailer_login')
    return render(request,"retailer_register.html")


def retailer_login(request):
    if request.method == "POST":
        name = request.POST.get('name')
        password = request.POST.get('password')

        # Simple login check (DB me check kar rahe hain)
        try:
            user = Retailer.objects.get(name=name, password=password)
            request.session['name'] = user.name
            request.session['user_type']="retailer"
            return redirect('retailer_dashboard')
        except Retailer.DoesNotExist:
            return render(request, 'retailer_login.html', {'error': 'Invalid credentials'})
    return render(request, "retailer_login.html")

# farmers product add and display

from django.shortcuts import render, redirect
from .models import Product

def add_product(request):
    if request.method == "POST":
        product = request.POST['product']
        description = request.POST['description']
        price = request.POST['price']
        quantity = request.POST['quantity']
        location = request.POST['location']
        image = request.FILES.get('image')

        # Current logged-in farmer ko get karo
        farmer_name = request.session.get('name')
        farmer = Farmer.objects.get(name=farmer_name)

        Product.objects.create(
            product=product,
            description=description,
            price=price,
            quantity=quantity,
            location=location,
            image=image,
            farmer=farmer  #  Ab product kis farmer ka hai ye store ho gaya
        )
        return redirect('show_products')

    return render(request, "add_product.html")

def show_products(request):
    farmer_name = request.session.get('name')
    farmer = Farmer.objects.get(name=farmer_name)
    products = Product.objects.filter(farmer=farmer)  #  sirf usi farmer ke products
    return render(request, "show_products.html", {"products": products})

def browse_products(request):
    products = Product.objects.all()
    return render(request, "browse_products.html", {"products":products})

def retailer_products(request):
    retailer_name = request.session.get('name')
    retailer = Retailer.objects.get(name=retailer_name)
    orders = Order.objects.filter(retailer=retailer)  #  sirf usi retailer ke orders
    return render(request, "retailer_products.html", {"orders": orders})

def place_order(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    retailer_name = request.session.get('name')
    retailer = Retailer.objects.get(name=retailer_name)

    # Product ke farmer ko directly use karo
    Order.objects.create(
        product=product,
        retailer=retailer,
        farmer=product.farmer,   # Corrected
        quantity=1,
        status="Pending"
    )

    return redirect('retailer_products')

def logout(request):
    request.session.flush()
    return redirect('home')

from django.shortcuts import render, get_object_or_404, redirect
from .models import Order

def track_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, "track_order.html", {"order": order})



# views.py
def farmer_order(request):
    if request.session.get("user_type") != "farmer":
        return redirect("farmer_login")

    farmer_name = request.session.get("name")
    farmer = Farmer.objects.get(name=farmer_name)
    orders = Order.objects.filter(farmer=farmer)  #  us farmer ke products ke orders

    return render(request, "farmer_order.html", {"orders": orders})


from django.shortcuts import redirect, get_object_or_404
from .models import Order

def update_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # Status ko agla stage dena
    if order.status == "Pending":
        order.status = "Accepted"
    elif order.status == "Accepted":
        order.status = "Packed"
    elif order.status == "Packed":
        order.status = "Dispatched"
    elif order.status == "Dispatched":
        order.status = "Delivered"

    order.save()
    return redirect('farmer_order')  # ya retailer_products jahan se click hua ho


from django.shortcuts import render, redirect, get_object_or_404
from .models import Order

def update_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == "POST":
        order.status = request.POST.get("status")
        lat = request.POST.get("current_lat")
        lng = request.POST.get("current_lng")

        if lat and lng:
            order.current_lat = float(lat)
            order.current_lng = float(lng)

        order.save()
        return redirect('farmer_order')  #  Farmer orders page par redirect karega

    return render(request, "update_status.html", {"order": order})





def chat_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    farmer = order.farmer
    retailer = order.retailer

    if request.method == "POST":
        msg = request.POST.get('message')
        if request.session.get('user_type') == "farmer":
            ChatMessage.objects.create(
                sender_farmer=farmer,
                receiver_retailer=retailer,
                message=msg
            )
        else:
            ChatMessage.objects.create(
                sender_retailer=retailer,
                receiver_farmer=farmer,
                message=msg
            )
        return redirect('chat', order_id=order_id)

    # Get all messages between this farmer and retailer
    messages = ChatMessage.objects.filter(
        (Q(sender_farmer=farmer, receiver_retailer=retailer) |
         Q(sender_retailer=retailer, receiver_farmer=farmer))
    ).order_by('timestamp')

    return render(request, "chat.html", {
        "order": order,
        "messages": messages
    })