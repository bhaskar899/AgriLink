from django.contrib.auth import authenticate
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


from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Farmer

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Farmer

def farmer_login(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        password = request.POST.get('password')

        try:
            user = Farmer.objects.get(name=name)
            if user.password == password:
                request.session['name'] = user.name
                request.session['user_type'] = 'farmer'
                request.session['profile_image'] = user.profile_image.url if user.profile_image else "/media/profiles/default.jpg"

                if user.first_login:
                    return redirect("training")
                return redirect("farmer_dashboard")
            else:
                messages.error(request, "Invalid password.")
        except Farmer.DoesNotExist:
            messages.error(request, "Invalid username.")

    return render(request, "farmer_login.html")




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

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Retailer # Assuming you import your model

from .models import Retailer

from .models import Retailer

def retailer_login(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        password = request.POST.get('password')

        try:
            user = Retailer.objects.get(name=name)
            if user.password == password:
                request.session['name'] = user.name
                request.session['user_type'] = 'retailer'
                request.session['profile_image'] = user.profile_image.url if user.profile_image else "/media/profiles/default.jpg"

                if user.first_login:
                    return redirect("training")
                return redirect("retailer_dashboard")
            else:
                messages.error(request, "Invalid password.")
        except Retailer.DoesNotExist:
            messages.error(request, "Invalid username.")

    return render(request, "retailer_login.html")

def logout(request):
    request.session.flush()
    return redirect('home')

# ---------- Farmer pages ----------
def farmer_dashboard(request):
    # simple dashboard - you can add stats later
    return render(request, "farmer_dashboard.html")

from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Farmer

def add_product(request):
    if request.method == "POST":
        farmer_name = request.session.get('name')
        if not farmer_name:
            return redirect('farmer_login')

        farmer = get_object_or_404(Farmer, name=farmer_name)

        product_name = request.POST.get('product', '').strip()
        description = request.POST.get('description', '').strip()
        price = request.POST.get('price') or 0
        quantity = request.POST.get('quantity') or 0
        location = request.POST.get('location', '').strip()
        image = request.FILES.get('image')

        # minimal validation
        if not product_name:
            return render(request, "add_product.html", {"error": "Product name is required."})

        p = Product.objects.create(
            product=product_name,
            description=description,
            price=float(price),
            quantity=int(quantity),
            location=location,
            image=image,
            farmer=farmer
        )
        # p.save() will call model save and do optimization
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

# views.py
# def update_status(request, order_id):
#     order = get_object_or_404(Order, id=order_id)
#     if request.method == "POST":
#         order.status = request.POST.get('status', order.status)
#         lat = request.POST.get('current_lat')
#         lng = request.POST.get('current_lng')
#         if lat and lng:
#             try:
#                 order.current_lat = float(lat)
#                 order.current_lng = float(lng)
#             except ValueError:
#                 pass
#         order.save()
#
#         # Notify all retailers (or specific retailer of the order)
#         retailer = order.retailer
#         Notification.objects.create(
#             sender=request.user,
#             receiver=retailer.user,  # assuming retailer.user points to User model
#             message=f"Order #{order.id} for {order.product.product} is now {order.status}."
#         )
#
#         return redirect('farmer_order')
#
#     return render(request, "update_status.html", {"order": order})
# ---------- Retailer pages ----------
def retailer_dashboard(request):
    return render(request, "retailer_dashboard.html")

from django.http import JsonResponse
from .models import Product
from django.shortcuts import render


# 🔥 Auto Suggest API
def ajax_search(request):
    query = request.GET.get("q", "")
    products = Product.objects.filter(
        product__istartswith=query
    ).values_list("product", flat=True)[:10]

    return JsonResponse(list(products), safe=False)


# 🔥 Browse Page — search + filter + min/max price
def browse_products(request):
    q = request.GET.get('q', '')
    loc = request.GET.get('location', '')
    min_p = request.GET.get('min_price', '')
    max_p = request.GET.get('max_price', '')

    products = Product.objects.all()

    # 🔍 Search
    if q:
        products = products.filter(product__icontains=q)

    # 📍 Location
    if loc:
        products = products.filter(location__icontains=loc)

    # 💰 Min price
    if min_p:
        products = products.filter(price__gte=min_p)

    # 💰 Max price
    if max_p:
        products = products.filter(price__lte=max_p)

    return render(request, "browse_products.html", {
        "products": products
    })


def track_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, "track_order.html", {"order": order})

# ---------- Notifications ----------
# def notifications(request):
#     user = request.user
#     notes = Notification.objects.filter(receiver=user).order_by('-timestamp')
#     return render(request, "notifications.html", {"notifications": notes})
#
# def mark_notification_read(request, nid):
#     n = get_object_or_404(Notification, id=nid, receiver=request.user)
#     n.is_read = True
#     n.save()
#     return redirect('notifications')
# ---------- Chat ----------
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from .models import ChatMessage
from django.views.decorators.csrf import csrf_exempt
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models import Q

from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from .models import ChatMessage


# projectapp/views.py (FIXED chat_view)

from .models import ChatMessage, Farmer, Retailer, Order

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages
from .models import ChatMessage, Order, Farmer, Retailer

# 🟢 Chat Page
from django.shortcuts import render, get_object_or_404, redirect
from .models import Order, Farmer, Retailer, ChatMessage, Notification

def chat_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    user_type = request.session.get("user_type")
    user_name = request.session.get("name")

    if user_type == "farmer":
        sender = get_object_or_404(Farmer, name=user_name)
    elif user_type == "retailer":
        sender = get_object_or_404(Retailer, name=user_name)
    else:
        return redirect("home")

    # Handle message sending
    if request.method == "POST":
        msg = request.POST.get("message", "").strip()
        img = request.FILES.get("image")

        if msg or img:
            if user_type == "farmer":
                ChatMessage.objects.create(order=order, sender_farmer=sender, message=msg, image=img)
                # Create notification for retailer
                if order.retailer:
                    Notification.objects.create(
                        sender_farmer=sender,
                        receiver_retailer=order.retailer,
                        message=f"New message from {sender.name} in Order #{order.id}"
                    )
            elif user_type == "retailer":
                ChatMessage.objects.create(order=order, sender_retailer=sender, message=msg, image=img)
                # Create notification for farmer
                if order.farmer:
                    Notification.objects.create(
                        sender_retailer=sender,
                        receiver_farmer=order.farmer,
                        message=f"New message from {sender.name} in Order #{order.id}"
                    )

        return redirect("chat", order_id=order_id)

    # Get all messages
    messages_list = ChatMessage.objects.filter(order=order).order_by("timestamp")

    # Mark seen for messages from the other participant
    for m in messages_list:
        if user_type == "farmer" and m.sender_retailer:
            m.seen = True
            m.save()
        elif user_type == "retailer" and m.sender_farmer:
            m.seen = True
            m.save()

    return render(request, "chat.html", {
        "order": order,
        "messages_list": messages_list,
        "user_type": user_type,
        "user_name": user_name,
        "sender": sender,  # pass sender to template for header
    })
# 🟡 Search API
def chat_search_api(request, order_id):
    q = request.GET.get("q", "").strip()
    msgs = ChatMessage.objects.filter(order_id=order_id)

    if q:
        msgs = msgs.filter(message__icontains=q)

    return JsonResponse({
        "results": [
            {
                "sender": m.sender_farmer.name if m.sender_farmer else m.sender_retailer.name,
                "message": m.message,
                "time": m.timestamp.strftime("%I:%M %p")
            } for m in msgs.order_by("timestamp")
        ]
    })


from .models import Order, ChatMessage, Farmer, Retailer
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
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings


def contact_submit(request):
    if request.method != "POST":
        return redirect("home")

    name = request.POST.get("name").strip()
    email = request.POST.get("email").strip()
    message_text = request.POST.get("message").strip()

    if not name or not email or not message_text:
        messages.error(request, "⚠ Please fill all fields.")
        return redirect("home")

    # Validate email
    try:
        validate_email(email)
    except:
        messages.error(request, "⚠ Invalid email address.")
        return redirect("home")

    subject = f"📩 New Contact Message from {name}"
    body = f"""
Name: {name}
Email: {email}

Message:
{message_text}
    """

    # ⭐ Retry logic added Karega 2 attempts
    for attempt in range(2):
        try:
            send_mail(
                subject,
                body,
                settings.EMAIL_HOST_USER,
                [settings.EMAIL_HOST_USER],
                fail_silently=False,
            )

            messages.success(request, "✅ Your message has been sent successfully!")
            return redirect("home")

        except Exception as e:
            last_error = str(e)

    # If both retries fail → show error
    messages.error(request, f"❌ Email failed even after retrying: {last_error}")
    return redirect("home")# views.py
# --- Training Views ---

def training(request):
    user_type = request.session.get('user_type')
    name = request.session.get('name')

    # Security Check: Must be logged in
    if not user_type or not name:
        messages.warning(request, "Please log in to continue.")
        return redirect("home")

    # Find the user object
    if user_type == "farmer":
        Model = Farmer
        dashboard_url = "farmer_dashboard"
    elif user_type == "retailer":
        Model = Retailer
        dashboard_url = "retailer_dashboard"
    else:
        return redirect("home")

    try:
        user = Model.objects.get(name=name)
    except Model.DoesNotExist:
        return redirect("home")

    # ⭐ CHECK: If already completed training, redirect to dashboard. ⭐
    # This prevents users who try to manually type the /training/ URL from seeing it again.
    if not user.first_login:
        return redirect(dashboard_url)

    # Show Training Page
    return render(request, "training.html")


def training_complete(request):
    name = request.session.get('name')
    user_type = request.session.get('user_type')

    if not name or not user_type:
        return redirect("home")

    try:
        if user_type == "farmer":
            user = Farmer.objects.get(name=name)
            redirect_url = "farmer_dashboard"
        elif user_type == "retailer":
            user = Retailer.objects.get(name=name)
            redirect_url = "retailer_dashboard"
        else:
            return redirect("home")

        # 🔥 CRITICAL: Update the user object to prevent showing training again
        user.first_login = False
        user.save()

        # Redirect to dashboard
        return redirect(redirect_url)

    except (Farmer.DoesNotExist, Retailer.DoesNotExist):
        return redirect("home")


from django.shortcuts import render, get_object_or_404, redirect
from .models import Farmer, Retailer, Driver

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Farmer, Retailer, Driver

from django.shortcuts import render, redirect, get_object_or_404
from .models import Farmer, Retailer, Driver
from django.contrib import messages

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Farmer, Retailer, Driver

# ===================== FARMER / RETAILER =====================
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Farmer, Retailer

# ===================== FARMER / RETAILER =====================
def profile(request):
    user_type = request.session.get("user_type")
    name = request.session.get("name")

    if user_type == "farmer":
        user = get_object_or_404(Farmer, name=name)
    else:
        user = get_object_or_404(Retailer, name=name)

    return render(request, "profile.html", {"user": user})

def profile_update(request):
    user_type = request.session.get("user_type")
    name = request.session.get("name")

    if user_type == "farmer":
        user = get_object_or_404(Farmer, name=name)
    else:
        user = get_object_or_404(Retailer, name=name)

    if request.method == "POST":
        user.name = request.POST.get("name")
        user.email = request.POST.get("email")
        user.contact = request.POST.get("contact")
        user.address = request.POST.get("address")

        if request.FILES.get("profile_image"):
            user.profile_image = request.FILES["profile_image"]

        user.save()
        request.session['profile_image'] = user.profile_image.url if user.profile_image else '/static/images/no-image.jpg'
        messages.success(request, "Profile updated successfully")
        return redirect("profile")

    return render(request, "profile_update.html", {"user": user})

def profile_delete(request):
    user_type = request.session.get("user_type")
    name = request.session.get("name")

    if user_type == "farmer":
        user = get_object_or_404(Farmer, name=name)
    else:
        user = get_object_or_404(Retailer, name=name)

    if request.method == "POST":
        user.delete()
        request.session.flush()
        messages.success(request, "Profile deleted successfully")
        return redirect("home")

    return render(request, "profile_delete.html", {"user": user})


# ===================== DRIVER =====================
def driver_profile(request):
    driver_id = request.session.get('id')
    if not driver_id:
        return redirect('driver_login')
    driver = get_object_or_404(Driver, id=driver_id)
    return render(request, "driver_profile.html", {"driver": driver})

def driver_profile_update(request):
    driver_id = request.session.get('id')
    if not driver_id:
        return redirect('driver_login')
    driver = get_object_or_404(Driver, id=driver_id)

    if request.method == "POST":
        driver.name = request.POST.get('name', driver.name)
        driver.phone = request.POST.get('phone', driver.phone)
        driver.location = request.POST.get('location', driver.location)
        driver.vehicle_number = request.POST.get('vehicle_number', driver.vehicle_number)
        driver.rate_per_km = float(request.POST.get('rate_per_km') or driver.rate_per_km)
        driver.capacity_kg = int(request.POST.get('capacity') or driver.capacity_kg)

        if request.FILES.get('driver_photo'):
            driver.driver_photo = request.FILES['driver_photo']
        if request.FILES.get('license_doc'):
            driver.license_doc = request.FILES['license_doc']

        driver.save()
        request.session['profile_image'] = driver.driver_photo.url if driver.driver_photo else '/static/images/no-image.jpg'
        messages.success(request, "Profile updated.")
        return redirect('driver_profile')

    return render(request, "driver_profile_update.html", {"driver": driver})

def driver_profile_delete(request):
    driver_id = request.session.get('id')
    if not driver_id:
        return redirect('driver_login')
    return render(request, "driver_profile_delete.html")

def driver_profile_delete_confirm(request):
    driver_id = request.session.get('id')
    if not driver_id:
        return redirect('driver_login')
    driver = get_object_or_404(Driver, id=driver_id)
    driver.delete()
    request.session.flush()
    return redirect('home')

def profile_delete_confirm(request):
    user_type = request.session.get("user_type")
    user_id = request.session.get("id")

    if not user_type or not user_id:
        return redirect('driver_login')

    if user_type == "farmer":
        user = get_object_or_404(Farmer, id=user_id)
    elif user_type == "retailer":
        user = get_object_or_404(Retailer, id=user_id)
    elif user_type == "driver":
        user = get_object_or_404(Driver, id=user_id)

    user.delete()
    request.session.flush()
    return redirect("home")


import random
from django.core.mail import send_mail
from django.contrib import messages
from django.shortcuts import render, redirect
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from .models import Farmer, Retailer


def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email").strip()

        # Validate email
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "⚠ Invalid email address.")
            return redirect("forgot_password")

        # Check Farmer OR Retailer
        user = None
        user_type = None

        if Farmer.objects.filter(email=email).exists():
            user = Farmer.objects.get(email=email)
            user_type = "farmer"

        elif Retailer.objects.filter(email=email).exists():
            user = Retailer.objects.get(email=email)
            user_type = "retailer"

        else:
            messages.error(request, "❌ Email not found!")
            return redirect("forgot_password")

        # Generate OTP
        otp = random.randint(100000, 999999)

        # Save in session
        request.session["reset_email"] = email
        request.session["reset_otp"] = otp
        request.session["reset_user_type"] = user_type

        # Send OTP email
        send_mail(
            subject="🔐 AgriLink Password Reset OTP",
            message=f"Your OTP for password reset is: {otp}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False,
        )

        messages.success(request, "📩 OTP sent to your email!")
        return redirect("verify_otp")

    return render(request, "forgot_password.html")


def verify_otp(request):
    if request.method == "POST":
        entered_otp = request.POST.get("otp")
        session_otp = str(request.session.get("reset_otp"))

        if entered_otp == session_otp:
            return redirect("reset_password")
        else:
            messages.error(request, "❌ Incorrect OTP!")
            return redirect("verify_otp")

    return render(request, "verify_otp.html")


def reset_password(request):
    if request.method == "POST":
        new_pass = request.POST.get("password")
        email = request.session.get("reset_email")
        user_type = request.session.get("reset_user_type")

        if user_type == "farmer":
            user = Farmer.objects.get(email=email)
        else:
            user = Retailer.objects.get(email=email)

        user.password = new_pass
        user.save()

        # Clear session
        del request.session["reset_email"]
        del request.session["reset_otp"]
        del request.session["reset_user_type"]

        messages.success(request, "✅ Password reset successful! Please login.")
        return redirect("farmer_login" if user_type == "farmer" else "retailer_login")

    return render(request, "reset_password.html")



def notifications_view(request):
    user_type = request.session.get('user_type')
    name = request.session.get('name')

    if user_type == 'farmer':
        user = Farmer.objects.get(name=name)
        notifications = Notification.objects.filter(receiver_farmer=user).order_by('-timestamp')
    elif user_type == 'retailer':
        user = Retailer.objects.get(name=name)
        notifications = Notification.objects.filter(receiver_retailer=user).order_by('-timestamp')

    return render(request, "notifications.html", {"notifications": notifications})

# projectapp/views.py (append these imports at the top)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.urls import reverse
from django.http import JsonResponse
from .models import Driver, Delivery, DriverNotification, Order, Product, Retailer, Farmer
from django.utils import timezone
import math

# Config: platform commission (5% default)
PLATFORM_COMMISSION = getattr(settings, 'PLATFORM_COMMISSION', 0.05)
####################################################33
# projectapp/views.py


from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse, FileResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.utils import timezone
import math

import razorpay

from .models import Product, Order, Retailer, Farmer, Driver, Delivery, Notification, DriverNotification

# ---------- PLACE ORDER ----------
def place_order(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # retailer must be logged in
    retailer_name = request.session.get('name')
    if not retailer_name or request.session.get('user_type') != 'retailer':
        messages.error(request, "Please login as Retailer to place an order.")
        return redirect('retailer_login')

    retailer = get_object_or_404(Retailer, name=retailer_name)

    if request.method == "POST":
        try:
            quantity = int(request.POST.get('quantity', '1'))
        except ValueError:
            messages.error(request, "Invalid quantity.")
            return redirect('place_order', product_id=product.id)

        contact = request.POST.get('contact', '').strip()
        address = request.POST.get('address', '').strip()

        if not contact or not address:
            messages.error(request, "Please provide address and contact.")
            return redirect('place_order', product_id=product.id)

        # create order (pending / not paid yet)
        order = Order.objects.create(
            product=product,
            quantity=quantity,
            retailer=retailer,
            contact=contact,
            address=address,
            farmer=product.farmer,
            status='Pending'
        )

        return redirect('payment_page', order_id=order.id)

    # GET -> show place_order form (template should include form with quantity/contact/address)
    return render(request, "place_order.html", {"product": product})


# ---------- PAYMENT PAGE ----------
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden
from django.contrib import messages
from .models import Order, Notification, Driver
from django.conf import settings
import razorpay

# ------------------------
# Payment Page
# ------------------------
def payment_page(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # ensure the session user is the retailer who created the order
    if request.session.get('user_type') != 'retailer' or request.session.get('name') != order.retailer.name:
        return HttpResponseForbidden("Not authorized.")

    amount_rupees = order.quantity * order.product.price   # total amount
    try:
        amount_paise = int(round(amount_rupees * 100))  # convert to paise
    except Exception:
        amount_paise = int(order.product.price * 100)

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    razorpay_order = client.order.create({
        "amount": amount_paise,
        "currency": "INR",
        "payment_capture": "1"
    })

    context = {
        "product": order.product,
        "order": order,
        "amount": amount_rupees,
        "razorpay_order_id": razorpay_order["id"],
        "razorpay_key": settings.RAZORPAY_KEY_ID,
    }
    return render(request, "payment_page.html", context)


# ------------------------
# Payment Success
# ------------------------
def payment_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # authorize retailer
    if request.session.get('user_type') != 'retailer' or request.session.get('name') != order.retailer.name:
        return HttpResponseForbidden("Not authorized.")

    if order.status != "Paid":
        order.status = "Paid"
        order.save()

        # Update product stock
        product = order.product
        if product.quantity is not None and product.quantity >= order.quantity:
            product.quantity -= order.quantity
            product.save()

        total_amount = order.quantity * product.price  # total paid by retailer

        # ----------------- Distribute Payment -----------------
        farmer_amount = total_amount * 0.95
        driver_amount = total_amount * 0.05 if order.driver else 0

        # Optional: Here you can integrate actual payment transfer logic to bank accounts

        # ------------- Notification to Farmer -------------
        Notification.objects.create(
            sender_retailer=order.retailer,
            receiver_farmer=order.farmer,
            message=f"Payment received for {order.quantity} kg of '{product.product}' by {order.retailer.name}. Amount credited: ₹{farmer_amount:.2f}"
        )

        # ------------- Notification to Driver (if driver exists) -------------
        if order.driver:
            Notification.objects.create(
                sender_retailer=order.retailer,
                receiver_driver=order.driver,
                message=f"You have received your delivery commission of ₹{driver_amount:.2f} for Order #{order.id}."
            )

        # Assign driver after payment (if your auto_assign_driver logic is needed)
        auto_assign_driver(order)

    return render(request, "payment_success.html", {"order": order})

# ------------------------
# Update Status (Farmer)
# ------------------------
def update_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == "POST":
        status = request.POST.get("status")
        order.status = status

        driver_id = request.POST.get("driver")
        assigned_driver = None
        if driver_id:
            driver = get_object_or_404(Driver, id=driver_id)
            order.driver = driver
            assigned_driver = driver  # store for notification/payment

        order.save()  # Save the updated order

        # ------------- Notification to retailer -------------
        Notification.objects.create(
            sender_farmer=order.farmer,
            receiver_retailer=order.retailer,
            message=f"Order #{order.id} status updated to '{order.status}' by {order.farmer.name}"
        )

        # ------------- Driver payment & notification -------------
        if assigned_driver and order.status.lower() != "pending":
            # Assuming total amount already paid by retailer
            total_amount = order.quantity * order.product.price
            driver_amount = total_amount * 0.05  # 5% commission

            # Optional: Integrate bank transfer logic here

            # Notification to driver
            Notification.objects.create(
                sender_farmer=order.farmer,
                receiver_driver=assigned_driver,
                message=f"You have received your delivery commission of ₹{driver_amount:.2f} for Order #{order.id}."
            )

        messages.success(request, "Order updated successfully!")
        return redirect("farmer_order")

    drivers = Driver.objects.all()
    return render(request, "update_status.html", {"order": order, "drivers": drivers})

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Notification, Farmer, Retailer, Driver

from django.shortcuts import render, get_object_or_404, redirect
from .models import Notification, Farmer, Retailer, Driver

def notifications(request):
    user_type = request.session.get('user_type')
    name = request.session.get('name')
    notes = []

    if user_type == "farmer" and name:
        user = Farmer.objects.filter(name=name).first()
        if user:
            notes = Notification.objects.filter(receiver_farmer=user).order_by('-timestamp')

    elif user_type == "retailer" and name:
        user = Retailer.objects.filter(name=name).first()
        if user:
            notes = Notification.objects.filter(receiver_retailer=user).order_by('-timestamp')

    elif user_type == "driver" and name:
        user = Driver.objects.filter(name=name).first()
        if user:
            notes = Notification.objects.filter(receiver_driver=user).order_by('-timestamp')

    return render(request, "notifications.html", {"notifications": notes})


def mark_notification_read(request, nid):
    user_type = request.session.get('user_type')
    name = request.session.get('name')

    if user_type == "farmer":
        user = Farmer.objects.filter(name=name).first()
        n = get_object_or_404(Notification, id=nid, receiver_farmer=user)
    elif user_type == "retailer":
        user = Retailer.objects.filter(name=name).first()
        n = get_object_or_404(Notification, id=nid, receiver_retailer=user)
    elif user_type == "driver":
        user = Driver.objects.filter(name=name).first()
        n = get_object_or_404(Notification, id=nid, receiver_driver=user)

    # mark as read
    n.is_read = True
    n.save()

    # Redirect to a relevant page depending on notification type
    # Here, you can customize based on message content
    # For example, if notification is about an order:
    if "Order" in n.message:
        order_id = n.message.split('#')[1].split()[0]  # Extract order id from message
        return redirect("order_detail", order_id=order_id)

    # default redirect back to notifications page
    return redirect("notifications")

def auto_assign_driver(order):
    if not order or not hasattr(order, 'id'):
        return None

    driver = Driver.objects.filter(is_available=True).first()
    if not driver:
        Notification.objects.create(
            receiver_farmer=order.farmer,
            message=f"No drivers available yet for Order #{order.id}."
        )
        return None

    estimated_distance_km = 10.0
    delivery_charge = round(estimated_distance_km * driver.rate_per_km, 2)

    platform_commission_pct = 0.20
    driver_earning = round(delivery_charge * (1 - platform_commission_pct), 2)

    delivery = Delivery.objects.create(
        order=order,
        driver=driver,
        distance_km=estimated_distance_km,
        delivery_charge=delivery_charge,
        driver_earning=driver_earning,
        status='assigned',
        assigned_at=timezone.now()
    )

    # update order
    order.driver = driver
    order.status = "Assigned to Driver"
    order.save()

    # make driver unavailable
    driver.is_available = False
    driver.save()

    # 🔔 NOTIFICATION -> DRIVER (for bell icon)
    Notification.objects.create(
        receiver_driver=driver,
        message=f"You have been assigned Order #{order.id}. Please check your dashboard."
    )

    # 🔔 notify farmer + retailer
    Notification.objects.create(
        receiver_farmer=order.farmer,
        message=f"Driver {driver.name} assigned for Order #{order.id}."
    )
    Notification.objects.create(
        receiver_retailer=order.retailer,
        message=f"Driver {driver.name} will deliver Order #{order.id}."
    )

    return delivery


def retailer_products(request):
    if request.session.get("user_type") != "retailer":
        return redirect("retailer_login")

    retailer_name = request.session.get('name')
    retailer = get_object_or_404(Retailer, name=retailer_name)

    orders = Order.objects.filter(retailer=retailer).order_by('-order_date')
    for o in orders:
        o.total_price = round(o.quantity * o.product.price, 2)

    return render(request, "retailer_products.html", {"orders": orders})


# ---------- DRIVER AUTH / DASHBOARD ----------
from django.contrib.auth import login as auth_login, logout as auth_logout

from django.contrib import messages
from .models import Driver

# views.py (driver_login)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Driver

# For Driver Login (same idea for Farmer/Retailer)
def driver_login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        try:
            driver = Driver.objects.get(email=email)
            if driver.password == password:
                request.session['id'] = driver.id
                request.session['user_type'] = 'driver'
                request.session['name'] = driver.name
                request.session['profile_image'] = driver.driver_photo.url if driver.driver_photo else '/static/images/no-image.jpg'
                return redirect('driver_dashboard')
            else:
                messages.error(request, "Incorrect password")
        except Driver.DoesNotExist:
            messages.error(request, "Driver not found")
    return render(request, "driver_login.html")



def driver_logout(request):
    request.session.flush()
    return redirect('home')


from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages


def driver_register(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        vehicle_type = request.POST.get('vehicle_type', 'tempo')
        Driver.objects.create(
            name=name, email=email, phone=phone, password=password,
            vehicle_type=vehicle_type, is_available=False
        )
        messages.success(request, "Driver registered. Please login.")
        return redirect('driver_login')
    return render(request, "driver_register.html")


def driver_dashboard(request):
    driver_id = request.session.get('id')
    if not driver_id:
        return redirect('driver_login')

    driver = get_object_or_404(Driver, id=driver_id)

    # Fetch orders assigned to this driver
    deliveries = Order.objects.filter(driver=driver).order_by('-id')

    # Count unread notifications if you want
    unread_notifications = Notification.objects.filter(receiver_driver=driver, is_read=False).count()

    return render(request, "driver_dashboard.html", {
        "driver": driver,
        "deliveries": deliveries,
        "unread_notifications": unread_notifications
    })


@require_POST
def driver_mark_picked(request, delivery_id): # <-- delivery_id का उपयोग करें
    if request.method == "POST":
        order = get_object_or_404(Order, id=delivery_id)
        # यह सुनिश्चित करता है कि 'packed' या 'assigned' के बाद ही स्टेटस 'picked' हो
        if order.status.lower() in ["assigned", "packed"]:
            order.status = "picked" # <-- यह अगला स्टेटस है
            order.save()
            # ... (rest of the code)
    return redirect('driver_dashboard')
# You should also update the driver_mark_delivered view for consistency:
def driver_mark_delivered(request, delivery_id): # <-- CHANGED TO delivery_id
    if request.method == "POST":
        order = get_object_or_404(Order, id=delivery_id)
        if order.status == "picked":
            order.status = "delivered"
            order.save()
            messages.success(request, f"Order #{order.id} marked as delivered.")
    return redirect('driver_dashboard')
# ---------- DRIVER: toggle availability (AJAX recommended) ----------
@require_POST
def driver_toggle_availability(request):
    if request.session.get('user_type') != 'driver':
        return JsonResponse({"error": "Not authorized"}, status=403)
    name = request.session.get('name')
    driver = get_object_or_404(Driver, name=name)
    is_avail = request.POST.get('is_available', 'false').lower() == 'true'
    driver.is_available = is_avail
    driver.save()
    return JsonResponse({"ok": True, "is_available": driver.is_available})


def driver_home(request):
    return render(request,"driver_home.html")


from .models import Delivery, Driver

def assign_driver(request, order_id):
    order = Order.objects.get(id=order_id)
    driver = Driver.objects.get(id=request.POST['driver_id'])

    # prevent duplicate assignment
    if Delivery.objects.filter(order=order).exists():
        messages.warning(request, "Delivery already exists for this order.")
        return redirect('order_detail', order_id=order_id)

    auto_assign_driver(order)
    messages.success(request, "Driver assigned and delivery created!")
    return redirect('order_detail', order_id=order_id)
