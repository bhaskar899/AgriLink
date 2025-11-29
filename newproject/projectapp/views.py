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




from django.core.mail import send_mail
import random


def retailer_register(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        contact = request.POST.get('contact')
        address = request.POST.get('address')
        gender = request.POST.get('gender')
        # Added missing fields from HTML template
        shop_number = request.POST.get('shop_number')
        gst_number = request.POST.get('gst_number')

        # 1) check if email already used
        if Retailer.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
            return redirect('retailer_register')

        # 2) create retailer (Assuming email_verified is set to False initially
        #    and verified later via the separate verify_email_otp view)
        retailer = Retailer.objects.create(
            name=name,
            email=email,
            password=password,
            contact=contact,
            address=address,
            gender=gender,
            shop_number=shop_number,  # Add these
            gst_number=gst_number,  # Add these
            email_verified=False,  # Keep this False until OTP is confirmed
            email_otp=None  # OTP should be handled by AJAX, not here
        )

        # 3) registration successful, send to login
        messages.success(request, "Registration successful. Please log in.")
        return redirect("retailer_login")  # <-- अब यह लॉगिन पेज पर जाएगा

    return render(request, "retailer_register.html")

# views.py

from django.http import JsonResponse
import json

# tasks.py
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_email_otp_async(subject, message, recipient_list):
    """Celery task to send email asynchronously."""
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
        fail_silently=False
    )
    # आप यहाँ logging भी जोड़ सकते हैं


# views.py (Required imports)
import random
import json
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect


# from .models import Retailer, ... (आपके अन्य मॉडल)


def send_email_otp(request):
    """OTP generate karta hai aur session mein store karke email bhejta hai."""
    if request.method == "POST":
        email = request.POST.get("email", "").strip()

        # Validation: Ensure email is provided (basic)
        if not email:
            return JsonResponse({"status": "error", "message": "Email not provided"})

        otp = str(random.randint(100000, 999999))

        # OTP aur Email dono ko session mein store karen
        request.session["email_otp"] = otp
        request.session["email_to_verify"] = email
        request.session['email_otp_verified'] = False  # Verification status reset

        try:
            # Note: Celery is required for fast asynchronous sending.
            # If not using Celery, this part will be synchronous and slow.
            send_mail(
                subject="Your Retailer Registration OTP",
                message=f"Your OTP for retailer registration is: {otp}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False
            )
            return JsonResponse({"status": "success", "message": "OTP sent successfully"})
        except Exception as e:
            # Handle mail sending errors
            print(f"Error sending email: {e}")
            return JsonResponse({"status": "error", "message": "Failed to send OTP email"})


def verify_email_otp(request):
    """User dwara entered OTP aur email ko session se check karta hai."""
    if request.method == "POST":
        try:
            # Data JSON format mein expect kar rahe hain (as sent by fetch in JS)
            data = json.loads(request.body)
            entered_otp = data.get("otp", "").strip()
            entered_email = data.get("email", "").strip()
        except Exception as e:
            # Fallback for form data (though JSON is preferred for fetch)
            entered_otp = request.POST.get("otp", "").strip()
            entered_email = request.POST.get("email", "").strip()

        # Session se sacha (true) OTP aur email lein
        saved_otp = request.session.get("email_otp")
        saved_email = request.session.get("email_to_verify")

        # Check if the entered OTP and the email match the saved values
        if saved_otp and entered_otp == saved_otp and entered_email == saved_email:
            # Verification successful, set a session flag
            request.session['email_otp_verified'] = True
            # OTP ko session se clear kar dena ek achhi practice hai
            # request.session.pop("email_otp", None)
            # request.session.pop("email_to_verify", None)
            return JsonResponse({"status": "success", "message": "Email OTP Verified"})
        else:
            return JsonResponse({"status": "error", "message": "Invalid OTP or Email Mismatch"})

    return JsonResponse({"status": "error", "message": "Invalid Request Method"})

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Retailer # Assuming you import your model

from .models import Retailer

from .models import Retailer


def retailer_login(request):
    if request.method == "POST":
        name = request.POST.get("name", '').strip()
        password = request.POST.get("password", '').strip()

        if not name or not password:
            messages.error(request, "Both username and password are required.")
            return redirect('retailer_login')

        try:
            retailer = Retailer.objects.get(name=name)

            if retailer.password.strip() == password.strip():
                request.session['name'] = retailer.name
                request.session['user_type'] = 'retailer'
                messages.success(request, "Login successful!")
                return redirect("retailer_dashboard")  # replace with your dashboard
            else:
                messages.error(request, "Invalid password.")
                return redirect('retailer_login')
        except Retailer.DoesNotExist:
            messages.error(request, "Retailer not found.")
            return redirect('retailer_login')

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

from django.shortcuts import render, get_object_or_404
from .models import Product, Farmer
import os
from django.conf import settings

def show_products(request):
    # Get farmer from session
    farmer_name = request.session.get('name')
    farmer = get_object_or_404(Farmer, name=farmer_name)

    # Delete products with quantity 0 along with image file
    products_to_delete = Product.objects.filter(farmer=farmer, quantity__lte=0)
    for product in products_to_delete:
        if product.image:
            # Delete image file from media folder
            image_path = os.path.join(settings.MEDIA_ROOT, product.image.name)
            if os.path.exists(image_path):
                os.remove(image_path)
        # Delete product from DB
        product.delete()

    # Get remaining products
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
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages



# .models import Driver
def driver_profile(request):
    driver_id = request.session.get('id')
    if not driver_id:
        return redirect('driver_login')

    driver = get_object_or_404(Driver, id=driver_id)
    # ❌ DriverProfile से संबंधित लाइन हटा दी गई है

    return render(request, "driver_profile.html", {"driver": driver})
    # टेम्पलेट को सिर्फ 'driver' ऑब्जेक्ट पास किया जाएगा


# .models import Driver
def driver_profile_update(request):
    driver_id = request.session.get('id')
    if not driver_id:
        return redirect('driver_login')

    driver = get_object_or_404(Driver, id=driver_id)
    # ❌ DriverProfile से संबंधित लाइन हटा दी गई है

    if request.method == "POST":
        # Driver fields
        driver.name = request.POST.get('name', driver.name)
        # ... (अन्य Driver fields) ...

        # ✅ License/Photo fields अब सीधे 'driver' पर सेव होंगे
        driver.license_issue_date = request.POST.get('license_issue_date') or driver.license_issue_date
        driver.license_expiry_date = request.POST.get('license_expiry_date') or driver.license_expiry_date

        if request.FILES.get('driver_photo'):
            driver.driver_photo = request.FILES['driver_photo']
        if request.FILES.get('license_doc'):
            driver.license_doc = request.FILES['license_doc']
        if request.FILES.get('vehicle_photo'):
            driver.vehicle_photo = request.FILES['vehicle_photo']

        driver.save()
        # ❌ profile.save() हटा दिया गया है

        messages.success(request, "Profile updated successfully!")
        return redirect('driver_profile')

    return render(request, "driver_profile_update.html", {"driver": driver})
    # टेम्पलेट को सिर्फ 'driver' ऑब्जेक्ट पास किया जाएगा

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
from .models import Delivery

def update_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == "POST":
        status = request.POST.get("status")
        order.status = status

        driver_id = request.POST.get("driver")

        # ✔ Driver Assign Logic + Delivery Create
        if driver_id and driver_id != "":
            driver = Driver.objects.get(id=driver_id)
            order.driver = driver
            order.save()

            delivery, created = Delivery.objects.get_or_create(order=order)
            delivery.driver = driver
            delivery.status = "assigned"
            delivery.save()

        order.save()

        Notification.objects.create(
            sender_farmer=order.farmer,
            receiver_retailer=order.retailer,
            message=f"Order #{order.id} status updated to {order.status}"
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
    n = None

    # 1. नोटिफ़िकेशन ऑब्जेक्ट को ढूंढें
    if user_type == "farmer":
        user = Farmer.objects.filter(name=name).first()
        n = get_object_or_404(Notification, id=nid, receiver_farmer=user)
    elif user_type == "retailer":
        user = Retailer.objects.filter(name=name).first()
        n = get_object_or_404(Notification, id=nid, receiver_retailer=user)
    elif user_type == "driver":
        user = Driver.objects.filter(name=name).first()
        n = get_object_or_404(Notification, id=nid, receiver_driver=user)

    if not n:
        return redirect("notifications")

    # 2. 'पढ़ा गया' (Read) मार्क करें
    n.is_read = True
    n.save()

    # 3. 🎯 अब नोटिफ़िकेशन गायब हो जाएगा!

    # 4. रीडायरेक्ट लॉजिक (सरलतम तरीका)

    # यदि आप चाहते हैं कि नोटिफ़िकेशन क्लिक होने पर ड्राइवर को सीधे 'ऑर्डर डिटेल्स' पर ले जाया जाए,
    # तो आप यहाँ ऑर्डर ID निकाल सकते हैं।

    # उदाहरण: यदि मैसेज में "Order #<ID>" है
    if user_type == "driver" and ("Order #" in n.message):
        try:
            order_id = n.message.split('#')[1].split()[0]
            return redirect("order_detail", order_id=order_id)
        except:
            pass  # अगर ID निकालने में कोई त्रुटि हो, तो default redirect पर जाएँ

    # 5. डिफ़ॉल्ट रूप से, नोटिफ़िकेशन पेज पर वापस रीडायरेक्ट करें
    return redirect("notifications")

from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.core.mail import send_mail
from .models import Driver, Notification, Delivery, Farmer, Retailer  # सुनिश्चित करें कि ये सभी import हों

from django.utils import timezone
from .models import Driver, Notification, Delivery  # सुनिश्चित करें कि सभी आवश्यक मॉडल import हैं


def auto_assign_driver(order):
    if not order or not hasattr(order, 'id'):
        return None

    # 1. ड्राइवर की उपलब्धता की जाँच करें
    driver = Driver.objects.filter(is_available=True).first()

    if not driver:
        # अगर कोई ड्राइवर उपलब्ध नहीं है, तो तुरंत Farmer को नोटिफ़ाई करके रुक जाएं
        Notification.objects.create(
            receiver_farmer=order.farmer,
            message=f"No drivers available yet for Order #{order.id}."
        )
        return None  # फ़ंक्शन यहीं रुक जाता है, असाइनमेंट नहीं होता

    # --- असाइनमेंट और गणना लॉजिक (केवल ड्राइवर उपलब्ध होने पर चलता है) ---

    # 2. गणना
    estimated_distance_km = 10.0
    delivery_charge = round(estimated_distance_km * driver.rate_per_km, 2)
    platform_commission_pct = 0.20
    driver_earning = round(delivery_charge * (1 - platform_commission_pct), 2)

    # 3. डिलीवरी रिकॉर्ड बनाएं
    delivery = Delivery.objects.create(
        order=order,
        driver=driver,
        distance_km=estimated_distance_km,
        delivery_charge=delivery_charge,
        driver_earning=driver_earning,
        status='assigned',
        assigned_at=timezone.now()
    )

    # 4. ऑर्डर और ड्राइवर की स्थिति अपडेट करें
    # auto_assign_driver फ़ंक्शन के अंदर

    # 4. ऑर्डर और ड्राइवर की स्थिति अपडेट करें
    order.driver = driver  # <--- यह लाइन सही है (Order में driver फ़ील्ड होना चाहिए)
    order.status = "Assigned to Driver"
    order.save()
    # ...
    # 💡 ड्राइवर को unavailable करें (यह बहुत महत्वपूर्ण है)
    driver.is_available = False
    driver.save()

    # 5. नोटिफ़िकेशन भेजें (केवल सफल असाइनमेंट के बाद)

    # 🔔 NOTIFICATION -> DRIVER (असाइनमेंट नोटिफ़िकेशन)
    Notification.objects.create(
        receiver_driver=driver,
        message=f"You have been assigned Order #{order.id}. Please check your dashboard."
    )

    # 🔔 NOTIFICATION -> FARMER
    Notification.objects.create(
        receiver_farmer=order.farmer,
        message=f"Driver {driver.name} assigned for Order #{order.id}."
    )

    # 🔔 NOTIFICATION -> RETAILER
    Notification.objects.create(
        receiver_retailer=order.retailer,
        message=f"Driver {driver.name} will deliver Order #{order.id}."
    )

    return delivery

# Payment (5% commission) Logic

# views.py या utils.py में होना चाहिए
# views.py या utils.py में होना चाहिए

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Order, Delivery  # सुनिश्चित करें कि Delivery मॉडल import हो रहा है


# 🌟 1. FIX: send_driver_payment_notification को import/define करें 🌟
# अगर आपने इसे utils.py में रखा है:
# from .utils import send_driver_payment_notification
#
# या अगर आप इसे इसी views.py फाइल में define कर रहे हैं:
def send_driver_payment_notification(order):
    from .models import Notification, Delivery

    # ✔ 1. Delivery record confirm karo
    delivery = Delivery.objects.filter(order=order).first()
    if not delivery:
        print("⚠ No Delivery record found!")
        return

    # ✔ 2. Driver confirm karo
    driver = delivery.driver
    if not driver:
        print("⚠ No driver found for this order!")
        return

    # ✔ 3. delivery_charge confirm karo
    delivery_charge = delivery.delivery_charge or 0
    if delivery_charge <= 0:
        delivery_charge = round((delivery.distance_km or 10) * (driver.rate_per_km or 12), 2)
        delivery.delivery_charge = delivery_charge
        delivery.save()

    # ✔ 4. 5% commission calculate
    commission = round(delivery_charge * 0.05, 2)

    # ✔ 5. Notification send
    Notification.objects.create(
        receiver_driver=driver,
        message=f"💰 Payment received for Order #{order.id}. Your 5% earning: ₹{commission}."
    )

    print(f"Notification sent to driver {driver.name}")

# आपका पेमेंट प्रोसेसिंग व्यू
def complete_order_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == "POST" and request.POST.get('payment_status') == 'SUCCESS':

        # Update order
        order.status = "Paid & Completed"
        order.save()

        # Delivery update
        delivery = Delivery.objects.filter(order=order).first()
        if delivery:
            delivery.status = "Completed"
            delivery.save()

        # ✔ FIX: Driver ko 5% earning notification
        send_driver_payment_notification(order)

        messages.success(request, f"Payment for Order #{order_id} complete.")
        return redirect('retailer_dashboard')

    messages.error(request, "Payment failed or not initiated.")
    return redirect('order_detail', order_id=order_id)



# views.py (या जहाँ भी आपका पेमेंट लॉजिक है)


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

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Driver  # सुनिश्चित करें कि यह आपके मॉडल को import करता है


def driver_register(request):
    if request.method == "POST":
        # 1. POST Data प्राप्त करें (Dates and Text Fields)
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')

        # Vehicle Details
        vehicle_number = request.POST.get('vehicle_number')
        # capacity और rate_per_km को int/float में बदलें (default values का उपयोग करके)
        capacity_kg = request.POST.get('capacity') or 1000
        rate_per_km = request.POST.get('rate_per_km') or 12.0
        location = request.POST.get('location')
        vehicle_type = request.POST.get('vehicle_type', 'tempo')  # यदि फ़ॉर्म में select field नहीं है

        # License Dates (जो अब Driver मॉडल में हैं)
        license_issue_date = request.POST.get('license_issue_date')
        license_expiry_date = request.POST.get('license_expiry_date')

        # 2. FILES Data प्राप्त करें (Images and Documents)
        # HTML फ़ॉर्म में 'license_image' और 'vehicle_image' नाम का उपयोग किया गया है
        license_doc_file = request.FILES.get('license_image')
        vehicle_photo_file = request.FILES.get('vehicle_image')

        # 3. Driver ऑब्जेक्ट बनाएं और सभी फ़ील्ड्स सेव करें
        Driver.objects.create(
            name=name,
            email=email,
            phone=phone,
            password=password,
            vehicle_type=vehicle_type,

            # Vehicle Details
            vehicle_number=vehicle_number,
            capacity_kg=int(capacity_kg),
            rate_per_km=float(rate_per_km),
            location=location,

            # Verification Fields
            license_doc=license_doc_file,  # 'license_image' को 'license_doc' फ़ील्ड में सेव करें
            vehicle_photo=vehicle_photo_file,  # 'vehicle_image' को 'vehicle_photo' फ़ील्ड में सेव करें
            license_issue_date=license_issue_date,
            license_expiry_date=license_expiry_date,

            # Default Status
            is_available=False,
            phone_verified=False  # default value
        )

        messages.success(request, "Driver registered. Please login.")
        return redirect('driver_login')

    # यदि GET Request है, तो रजिस्ट्रेशन फ़ॉर्म दिखाएँ
    # नोट: आपको VEHICLE_CHOICES पास करने की आवश्यकता हो सकती है यदि आप ड्रॉपडाउन का उपयोग करते हैं
    return render(request, "driver_register.html")



from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import Order, Delivery  # सुनिश्चित करें कि Delivery मॉडल import है


# views.py (Updated driver_mark_picked)

@require_POST
def driver_mark_picked(request, delivery_id):
    delivery = get_object_or_404(Delivery, id=delivery_id)
    order = delivery.order

    if delivery.status == 'assigned':

        # A. Delivery स्टेटस अपडेट करें
        delivery.status = 'picked'
        delivery.picked_at = timezone.now()
        delivery.save()

        # B. Order स्टेटस अपडेट करें
        order.status = "Picked"
        order.save()

        messages.success(request, f"Order #{order.id} is picked and is now in transit.")
    else:
        messages.warning(request, f"Cannot mark picked. Current status: {delivery.status}")

    # 💡 Note: URL कंसिस्टेंसी के लिए 'driver_assigned_deliveries' की जगह 'driver_deliveries' उपयोग करें
    return redirect('driver_deliveries')


# You should also update the driver_mark_delivered view for consistency:
# views.py (Updated driver_mark_delivered)

# views.py (Updated driver_mark_delivered)

@require_POST
def driver_mark_delivered(request, delivery_id):
    delivery = get_object_or_404(Delivery, id=delivery_id)
    order = delivery.order

    if delivery.status == "picked":

        # ✔ Correct Delivery Status
        delivery.status = "delivered"
        delivery.delivered_at = timezone.now()
        delivery.save()

        # ✔ Correct Order Status
        order.status = "Delivered"
        order.save()

        # ✔ Make Driver Available
        driver = delivery.driver
        if driver:
            driver.is_available = True
            driver.save()

        # ✔ Notification to Retailer
        Notification.objects.create(
            receiver_retailer=order.retailer,
            message=f"Order #{order.id} has been delivered successfully!"
        )

        messages.success(request, f"Order #{order.id} marked as Delivered!")

    else:
        messages.warning(
            request,
            f"Order #{order.id} must be 'picked' before marking as Delivered. Current: {delivery.status}"
        )

    return redirect("driver_deliveries")


def driver_toggle_availability(request):
    if request.method == "POST":
        driver_id = request.session.get("id")
        driver = get_object_or_404(Driver, id=driver_id)

        is_available = request.POST.get("is_available") == "true"
        driver.is_available = is_available
        driver.save()

        return JsonResponse({"ok": True, "is_available": driver.is_available})

    return JsonResponse({"ok": False})

def driver_home(request):
    return render(request,"driver_home.html")


from .models import Delivery, Driver


# views.py (Updated assign_driver)

# views.py (Corrected assign_driver logic)
from django.utils import timezone

# views.py (Corrected assign_driver)
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

# views.py (assign_driver)
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone


# सुनिश्चित करें कि आपके सभी मॉडल यहां imported हैं

def assign_driver(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        driver = get_object_or_404(Driver, id=request.POST['driver_id'])

        if Delivery.objects.filter(order=order).exists():
            messages.warning(request, "Delivery already exists for this order.")
            return redirect('order_detail', order_id=order_id)

        # ------------------------------
        # ⭐ CORRECT EARNING CALCULATION
        # ------------------------------
        retailer_amount = order.product.price * order.quantity
        driver_earning = round(retailer_amount * 0.05, 2)  # 5% earning
        delivery_charge = retailer_amount                  # retailer pays only product amount

        # ------------------------------
        # Create Delivery
        # ------------------------------
        delivery = Delivery.objects.create(
            order=order,
            driver=driver,
            status='assigned',
            assigned_at=timezone.now(),
            distance_km=0.0,
            delivery_charge=delivery_charge,
            driver_earning=driver_earning
        )

        # Order status update
        order.status = "Assigned to Driver"
        order.save()

        # Driver offline
        driver.is_available = False
        driver.save()

        # ⭐ DRIVER NOTIFICATION — वापस enabled
        DriverNotification.objects.create(
            driver=driver,
            message=f"New delivery assigned! Order #{order.id}. Your earning: ₹{driver_earning}"
        )

        messages.success(request, f"Order #{order.id} successfully assigned to {driver.name}.")
        return redirect('order_detail', order_id=order_id)

    return redirect('order_detail', order_id=order_id)


from django.core.mail import send_mail
from django.contrib import messages
from .models import Driver
import random

from django.core.mail import send_mail
from django.contrib import messages
import random

from django.core.mail import send_mail
from django.shortcuts import redirect
import random

import random
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.contrib import messages


# NOTE: This version sends the OTP via email, as per the original code.
def send_mobile_otp(request):  # Renamed function for clarity
    if request.method == "POST":
        email = request.POST.get("email")
        phone = request.POST.get("phone")

        # 1. Start by redirecting to the OTP page regardless of success/failure
        # This prevents email/phone enumeration
        redirect_to_otp = redirect("verify_driver_otp")

        try:
            driver = Driver.objects.get(email=email, phone=phone)
            # If the driver object is found (email AND phone match)
        except Driver.DoesNotExist:
            # If email/phone pair is invalid, still redirect to OTP page
            # but do not send OTP.
            return redirect_to_otp

        # 2. Generate and Store OTP (Temporarily using session as per original code)
        otp = random.randint(100000, 999999)
        request.session['driver_otp'] = otp
        request.session['otp_email'] = driver.email

        # 3. Send OTP
        try:
            send_mail(
                subject="Your OTP for Driver Verification",
                message=f"Your OTP is: {otp}. It is valid for 10 minutes.",
                from_email=None,
                recipient_list=[driver.email],
                fail_silently=True  # Changed to True to avoid exposing server errors
            )
        except Exception:
            # If mail fails, silently fail and return to OTP page.
            # Ideally, log the error here.
            pass

        # Always redirect to the OTP verification page
        return redirect_to_otp

    # Add a GET request handler if needed, usually redirecting to an input form
    return redirect("otp_input_form")  # Assuming a URL where email/phone is entered


# .models से अब सिर्फ Driver को import करें (यदि आपने मॉडल मर्ज कर दिया है)
# from .models import Driver
# (DriverProfile की कोई आवश्यकता नहीं है)

def verify_driver_otp(request):
    if request.method == "POST":
        entered_otp = request.POST.get("otp")
        session_otp = request.session.get("driver_otp")

        if str(entered_otp) == str(session_otp):
            # OTP verified
            email = request.session.get("otp_email")
            driver = Driver.objects.get(email=email)

            # --- 🌟 यह अपडेट किया गया कोड है 🌟 ---
            # अब phone_verified सीधे Driver ऑब्जेक्ट पर सेट किया जाएगा
            driver.phone_verified = True
            driver.save()
            # -----------------------------------

            messages.success(request, "Phone number verified successfully!")
            # Clear session
            del request.session['driver_otp']
            del request.session['otp_email']

            return redirect("driver_profile")
        else:
            messages.error(request, "Incorrect OTP. Try again.")
            return redirect("verify_driver_otp")

    return render(request, "verify_driver_otp.html")


# views.py (उदाहरण)

from django.shortcuts import render
from datetime import date


# Assume you have Order model, and order has driver_id, gross_fee, commission fields

# views.py (Real-World Dashboard)

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from datetime import date, timedelta
from .models import Driver, Order, Notification, Delivery  # सुनिश्चित करें कि ये सभी import हों

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from datetime import date, timedelta
from .models import Driver, Order, Notification  # सुनिश्चित करें कि Delivery मॉडल भी imported है (आपके मॉडल से)
from django.db.models import Q  # अगर आपको OR conditions की जरूरत पड़े

# views.py (driver_dashboard)

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, F
from datetime import date, timedelta
from .models import Driver, Order, Notification, Delivery  # सुनिश्चित करें कि Delivery मॉडल import है


# your_app_name/views.py

# views.py (driver_dashboard)
from datetime import date, timedelta
from django.db.models import Sum


# views.py
from django.db.models import Sum
from datetime import timedelta, date
from django.utils import timezone

def driver_dashboard(request):
    driver_id = request.session.get("id")
    if not driver_id:
        return redirect("driver_login")

    driver = get_object_or_404(Driver, id=driver_id)

    # -------------------------
    #  REAL TIME CALCULATIONS
    # -------------------------

    # Total earnings (all delivered)
    total_earnings = (
        Delivery.objects.filter(driver=driver, status="delivered")
        .aggregate(sum=Sum("driver_earning"))["sum"] or 0.0
    )

    # Pending payout
    pending_payout = (
        Delivery.objects.filter(driver=driver, status="delivered", is_paid_out=False)
        .aggregate(sum=Sum("driver_earning"))["sum"] or 0.0
    )

    # Weekly deliveries
    one_week_ago = timezone.now() - timedelta(days=7)
    weekly_deliveries = Delivery.objects.filter(
        driver=driver,
        status="delivered",
        delivered_at__gte=one_week_ago
    ).count()

    # Last 5 deliveries
    delivery_history = Delivery.objects.filter(
        driver=driver, status="delivered"
    ).order_by("-delivered_at")[:5]

    context = {
        "driver": driver,
        "total_earnings": f"{total_earnings:.2f}",
        "pending_payout": f"{pending_payout:.2f}",
        "weekly_deliveries": weekly_deliveries,
        "delivery_history": delivery_history,
    }

    return render(request, "driver_dashboard.html", context)


from django.shortcuts import render, redirect
from django.db.models import Count


# मान लीजिए आपके पास Order और Notification मॉडल हैं

# your_app_name/views.py (अंतिम भाग)

# ... (अन्य views) ...

# your_app_name/views.py

from django.shortcuts import render, redirect, get_object_or_404
from .models import Driver, Notification, Order, Retailer  # सुनिश्चित करें कि सभी आवश्यक मॉडल import हैं


# ... (driver_dashboard फ़ंक्शन के बाद) ...

# views.py (driver_assigned_deliveries)

# projectapp/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
# सुनिश्चित करें कि आपके सभी आवश्यक मॉडल import हैं
from .models import Driver, Delivery, Notification, Order, Retailer, Farmer

# projectapp/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
# सुनिश्चित करें कि आपके सभी आवश्यक मॉडल import हैं
from .models import Driver, Delivery, Notification


from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import Delivery, Notification, Driver

def driver_assigned_deliveries(request):
    driver_id = request.session.get('id')
    if not driver_id:
        return redirect('driver_login')

    driver = get_object_or_404(Driver, id=driver_id)

    # 👉 Only active deliveries (Assigned or Picked)
    active_deliveries = Delivery.objects.filter(
        driver=driver
    ).exclude(
        Q(status__iexact='delivered') | Q(status__iexact='canceled')
    ).select_related('order', 'order__product', 'order__retailer')

    unread_notifications = Notification.objects.filter(receiver_driver=driver, is_read=False).count()

    context = {
        'deliveries': active_deliveries,
        'driver': driver,
        'unread_notifications': unread_notifications,
    }
    return render(request, "driver_assigned_deliveries.html", context)

def update_delivery_status(request, delivery_id):
    delivery = get_object_or_404(Delivery, id=delivery_id)

    if request.method == "POST":
        new_status = request.POST.get("status")

        if new_status == "delivered":
            delivery.status = "delivered"
            delivery.delivered_at = timezone.now()

            # ⭐ Driver earning bhi tab consider hoti hai
            # ⭐ Payout pending hi rahega, jab admin pay kare tab paid hoga

            delivery.save()

            # agar order hai to uska status bhi update karo
            delivery.order.status = "Delivered"
            delivery.order.save()

            messages.success(request, "Delivery marked as completed.")
            return redirect("driver_dashboard")

        # Baaki statuses ke liye
        delivery.status = new_status
        delivery.save()
        return redirect("driver_dashboard")