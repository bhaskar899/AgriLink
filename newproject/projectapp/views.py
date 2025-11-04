from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from .models import Farmer, Retailer, Product, Order, ChatMessage, Notification
from django.core.mail import send_mail
from django.conf import settings

# Basic pages
def master(request):
    return render(request, "master.html")

def home(request):
    return render(request, "home.html")

def about(request):
    return render(request, "about.html")

def contact(request):
    return render(request, "contact.html")

# ---------- Authentication (simple session-based) ----------
def farmer_register(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        contact = request.POST.get('contact')
        address = request.POST.get('address')
        gender = request.POST.get('gender')
        Farmer.objects.create(name=name, email=email, password=password, contact=contact, address=address, gender=gender)
        return redirect('farmer_login')
    return render(request, "farmer_register.html")

def farmer_login(request):
    error = None
    if request.method == "POST":
        name = request.POST.get('name')
        password = request.POST.get('password')
        try:
            user = Farmer.objects.get(name=name, password=password)
            request.session['name'] = user.name
            request.session['user_type'] = 'farmer'
            return redirect('farmer_dashboard')
        except Farmer.DoesNotExist:
            error = "Invalid credentials"
    return render(request, "farmer_login.html", {'error': error})

def retailer_register(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        contact = request.POST.get('contact')
        address = request.POST.get('address')
        gender = request.POST.get('gender')
        Retailer.objects.create(name=name, email=email, password=password, contact=contact, address=address, gender=gender)
        return redirect('retailer_login')
    return render(request, "retailer_register.html")

def retailer_login(request):
    error = None
    if request.method == "POST":
        name = request.POST.get('name')
        password = request.POST.get('password')
        try:
            user = Retailer.objects.get(name=name, password=password)
            request.session['name'] = user.name
            request.session['user_type'] = 'retailer'
            return redirect('retailer_dashboard')
        except Retailer.DoesNotExist:
            error = "Invalid credentials"
    return render(request, "retailer_login.html", {'error': error})

def logout(request):
    request.session.flush()
    return redirect('home')

# ---------- Farmer pages ----------
def farmer_dashboard(request):
    # simple dashboard - you can add stats later
    return render(request, "farmer_dashboard.html")

def add_product(request):
    if request.method == "POST":
        farmer_name = request.session.get('name')
        farmer = get_object_or_404(Farmer, name=farmer_name)
        product = request.POST.get('product')
        description = request.POST.get('description')
        price = request.POST.get('price') or 0
        quantity = request.POST.get('quantity') or 0
        location = request.POST.get('location')
        image = request.FILES.get('image')
        Product.objects.create(product=product, description=description, price=float(price), quantity=int(quantity), location=location, image=image, farmer=farmer)
        return redirect('show_products')
    return render(request, "add_product.html")

def show_products(request):
    farmer_name = request.session.get('name')
    farmer = get_object_or_404(Farmer, name=farmer_name)
    products = Product.objects.filter(farmer=farmer)
    return render(request, "show_products.html", {"products": products})

def farmer_order(request):
    # list orders for this logged-in farmer
    if request.session.get("user_type") != "farmer":
        return redirect("farmer_login")
    farmer_name = request.session.get("name")
    farmer = get_object_or_404(Farmer, name=farmer_name)
    orders = Order.objects.filter(farmer=farmer).order_by('-order_date')
    return render(request, "farmer_order.html", {"orders": orders})

def update_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == "POST":
        # example: form sends 'status', 'current_lat', 'current_lng'
        order.status = request.POST.get('status', order.status)
        lat = request.POST.get('current_lat')
        lng = request.POST.get('current_lng')
        if lat and lng:
            try:
                order.current_lat = float(lat)
                order.current_lng = float(lng)
            except ValueError:
                pass
        order.save()

        # notify retailer
        Notification.objects.create(
            user_type='retailer',
            user_name=order.retailer.name,
            message=f"Your order #{order.id} for {order.product.product} is now {order.status}."
        )
        return redirect('farmer_order')

    # For GET: show a simple update page (create template update_status.html)
    return render(request, "update_status.html", {"order": order})

# ---------- Retailer pages ----------
def retailer_dashboard(request):
    return render(request, "retailer_dashboard.html")

def browse_products(request):
    q = request.GET.get('q', '')
    loc = request.GET.get('location', '')
    products = Product.objects.all()
    if q:
        products = products.filter(product__icontains=q)
    if loc:
        products = products.filter(location__icontains=loc)
    return render(request, "browse_products.html", {"products": products})


from django.shortcuts import render, redirect, get_object_or_404


from .models import Product, Order # Assuming Product and Order are your models

# =========================================================
#  CORRECTED place_order FUNCTION in projectapp/views.py
# =========================================================

from django.shortcuts import render, redirect, get_object_or_404
# You MUST import your models here:
from .models import Product, Order


# The CORRECT way (Using the new order's ID for the redirect)
from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Order, Retailer

from django.shortcuts import get_object_or_404, redirect
from .models import Product, Retailer, Order

from django.shortcuts import get_object_or_404, redirect
from .models import Product, Retailer

def retailer_products(request):
    if request.session.get("user_type") != "retailer":
        return redirect("retailer_login")

    retailer_name = request.session.get('name')
    retailer = get_object_or_404(Retailer, name=retailer_name)

    # ✅ Load all orders of this retailer
    orders = Order.objects.filter(retailer=retailer).order_by('-order_date')

    # ✅ Dynamically calculate total price
    for o in orders:
        o.total_price = o.quantity * o.product.price

    return render(request, "retailer_products.html", {"orders": orders})

def track_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, "track_order.html", {"order": order})

# ---------- Notifications ----------
def notifications(request):
    name = request.session.get('name')
    user_type = request.session.get('user_type')
    if not name or not user_type:
        return redirect('home')
    notes = Notification.objects.filter(user_name=name, user_type=user_type).order_by('-timestamp')
    return render(request, "notifications.html", {"notifications": notes})

# mark notification read (optional)
def mark_notification_read(request, nid):
    n = get_object_or_404(Notification, id=nid)
    n.is_read = True
    n.save()
    return redirect('notifications')

# ---------- Chat ----------
def chat_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    farmer = order.farmer
    retailer = order.retailer

    if request.method == "POST":
        msg_text = request.POST.get('message')
        if request.session.get('user_type') == 'farmer':
            ChatMessage.objects.create(sender_farmer=farmer, receiver_retailer=retailer, message=msg_text)
        else:
            ChatMessage.objects.create(sender_retailer=retailer, receiver_farmer=farmer, message=msg_text)
        return redirect('chat', order_id=order_id)

    # fetch all messages between these two
    messages = ChatMessage.objects.filter(
        (Q(sender_farmer=farmer, receiver_retailer=retailer) |
         Q(sender_retailer=retailer, receiver_farmer=farmer))
    ).order_by('timestamp')

    return render(request, "chat.html", {"order": order, "messages": messages})


#Payment Method
# =========================================================
# Your EXISTING Payment Methods in views.py (No changes needed)
# =========================================================
#Payment Method
import razorpay
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from .models import Order # Ensure 'Order' is imported

import razorpay
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Order, Retailer

import razorpay
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Retailer, Order

from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
import razorpay
from .models import Product, Order, Retailer


# 🟢 Step 1: When retailer clicks "Buy Now"
# =========================
# UPDATED place_order view
# =========================
from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Retailer, Order

from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Order, Retailer

# 🟢 Step 1: Place Order (Retailer form submission)
def place_order(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    retailer_name = request.session.get('name')

    if not retailer_name:
        return redirect('retailer_login')

    retailer = get_object_or_404(Retailer, name=retailer_name)

    if request.method == "POST":
        quantity = int(request.POST.get('quantity'))
        address = request.POST.get('address')
        contact = request.POST.get('contact')

        # 🧮 Calculate total price
        total_amount = product.price * quantity

        # ✅ Create a temporary order (Pending payment)
        order = Order.objects.create(
            product=product,
            retailer=retailer,
            farmer=product.farmer,
            quantity=quantity,
            status='Pending'
        )

        # 🧭 Redirect to payment page, including order ID
        return redirect('payment_page', order_id=order.id)

    return render(request, "place_order.html", {"product": product})


# 🟢 Step 2: Payment Page (Razorpay checkout)
def payment_page(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    product = order.product

    # 🧮 Calculate total price dynamically
    amount = int(order.quantity * product.price)  # ₹ → convert to integer rupees
    amount_paise = amount * 100  # Razorpay needs paise

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    payment_order = client.order.create({
        "amount": amount_paise,
        "currency": "INR",
        "payment_capture": "1"
    })

    context = {
        "product": product,
        "order": order,
        "amount": amount,
        "razorpay_order_id": payment_order["id"],
        "razorpay_key": settings.RAZORPAY_KEY_ID,
    }

    return render(request, "payment_page.html", context)

# ✅ Payment success view (final version)
from django.shortcuts import render, redirect, get_object_or_404
from .models import Order, Product

from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
from .models import Order, Product, Notification

from django.http import FileResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
from .models import Order, Product, Notification

def payment_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # ✅ Mark as paid if not already
    if order.status != "Paid":
        order.status = "Paid"
        order.save()

        # ✅ Reduce product quantity
        product = order.product
        if product.quantity >= order.quantity:
            product.quantity -= order.quantity
            product.save()

        # ✅ Notify farmer
        Notification.objects.create(
            user_type="farmer",
            user_name=product.farmer.name,
            message=f"Your product '{product.product}' was purchased by {order.retailer.name}."
        )

    return render(request, "payment_success.html", {"order": order})

def generate_receipt(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    p.setTitle("AgriLink Receipt")

    # Header
    p.setFont("Helvetica-Bold", 18)
    p.drawString(200, 800, "AgriLink Payment Receipt")

    # Details
    p.setFont("Helvetica", 12)
    p.drawString(50, 760, f"Order ID: #{order.id}")
    p.drawString(50, 740, f"Retailer Name: {order.retailer.name}")
    p.drawString(50, 720, f"Product: {order.product.product}")
    p.drawString(50, 700, f"Farmer: {order.farmer.name}")
    p.drawString(50, 680, f"Quantity: {order.quantity} kg")
    p.drawString(50, 660, f"Price per kg: ₹{order.product.price}")
    p.drawString(50, 640, f"Total Amount: ₹{order.quantity * order.product.price}")
    p.drawString(50, 620, "Payment Status: Paid ✅")

    # Footer
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(50, 580, "Thank you for purchasing via AgriLink.")
    p.drawString(50, 565, "Contact: support@agrilink.com")

    p.showPage()
    p.save()
    buffer.seek(0)

    return FileResponse(buffer, as_attachment=True, filename=f"AgriLink_Receipt_Order_{order.id}.pdf")




from django.shortcuts import render

# def contact(request):
#     if request.method == "POST":
#         name = request.POST.get("name")
#         email = request.POST.get("email")
#         message = request.POST.get("message")
#
#         send_mail(
#             subject=f"📩 New Contact from {name}",
#             message=f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}",
#             from_email=settings.EMAIL_HOST_USER,
#             recipient_list=[settings.EMAIL_HOST_USER],
#             fail_silently=False,
#         )
#         return render(request, "master.html", {"success": True})
#     return render(request, "master.html")


from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings

def contact_submit(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        try:
            send_mail(
                subject=f"📩 New Contact Message from {name}",
                message=f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[settings.EMAIL_HOST_USER],
                fail_silently=False,
            )
            messages.success(request, "✅ Your message was sent successfully!")
        except Exception as e:
            print("EMAIL ERROR:", e)   # 👈 Add this line
            messages.error(request, f"⚠ Error sending email: {e}")
        return redirect('home')

    return redirect('home')