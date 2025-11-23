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
    if request.method == 'POST':
        name = request.POST.get('name')
        password = request.POST.get('password')

        try:
            user = Farmer.objects.get(name=name)

            if user.password == password:

                # STORE SESSION DATA
                request.session['name'] = user.name
                request.session['user_type'] = 'farmer'

                # ⭐ ADD THIS - Store profile image in session
                if user.profile_image:
                    request.session['profile_image'] = user.profile_image.url
                else:
                    request.session['profile_image'] = "/media/profiles/default.jpg"

                # REDIRECT BASED ON FIRST LOGIN
                if user.first_login:
                    return redirect("training")
                else:
                    return redirect("farmer_dashboard")

        except Farmer.DoesNotExist:
            messages.error(request, "Invalid username or password.")

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

def retailer_login(request):
    error = None

    if request.method == "POST":
        name = request.POST.get('name')
        password = request.POST.get('password')

        try:
            user = Retailer.objects.get(name=name, password=password)

            # Session set
            request.session['name'] = user.name
            request.session['user_type'] = 'retailer'

            # ⭐ ADD THIS - Store profile image in session
            if user.profile_image:
                request.session['profile_image'] = user.profile_image.url
            else:
                request.session['profile_image'] = "/media/profiles/default.jpg"

            # First login check
            if user.first_login:
                return redirect('training')

            return redirect('retailer_dashboard')

        except Retailer.DoesNotExist:
            messages.error(request, "Invalid credentials")

    return render(request, "retailer_login.html", {'error': error})
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


def profile(request):
    user_type = request.session.get("user_type")
    name = request.session.get("name")

    if user_type == "farmer":
        user = Farmer.objects.get(name=name)
    else:
        user = Retailer.objects.get(name=name)

    return render(request, "profile.html", {"user": user})


def profile_update(request):
    user_type = request.session.get("user_type")
    name = request.session.get("name")

    if user_type == "farmer":
        user = Farmer.objects.get(name=name)
    else:
        user = Retailer.objects.get(name=name)

    if request.method == "POST":
        user.name = request.POST.get("name")
        user.email = request.POST.get("email")
        user.contact = request.POST.get("contact")
        user.address = request.POST.get("address")

        if request.FILES.get("profile_image"):
            user.profile_image = request.FILES["profile_image"]

        user.save()

        # ⭐ SESSION UPDATE FIX
        request.session['profile_image'] = user.profile_image.url

        return redirect("profile")

    return render(request, "profile_update.html", {"user": user})

def profile_delete(request):
    return render(request, "profile_delete.html")


def profile_delete_confirm(request):
    user_type = request.session.get("user_type")
    name = request.session.get("name")

    if user_type == "farmer":
        user = Farmer.objects.get(name=name)
    else:
        user = Retailer.objects.get(name=name)

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





