from django.contrib.auth import authenticate
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from .models import Farmer, Retailer, Product, Order, ChatMessage, Notification, Sale, SampleRequest
from django.core.mail import send_mail
from django.conf import settings

# Basic pages
def master(request):
    return render(request, "master.html")


from .models import RetailerSampleReview


from .models import SampleRequest  # ya jo model tumhare reviews ka hai

from django.db.models import Avg
from .models import SampleRequest

def home(request):
    reviews = SampleRequest.objects.all().order_by('-id')[:10]  # latest 10 reviews
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0

    return render(request, "home.html", {
        "reviews": reviews,
        "avg_rating": round(avg_rating, 1),  # one decimal
    })
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
                # Save id in session
                request.session['id'] = user.id
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

from celery import shared_task
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
                # ✅ Save retailer id in session for future requests
                request.session['id'] = retailer.id       # <-- important
                request.session['name'] = retailer.name
                request.session['user_type'] = 'retailer'

                messages.success(request, "Login successful!")
                return redirect("retailer_dashboard")
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
    # Check login session
    if request.session.get("user_type") != "farmer":
        return redirect("farmer_login")

    farmer_name = request.session.get("name")
    farmer = get_object_or_404(Farmer, name=farmer_name)

    # ✅ FIXED: Show ALL orders including delivered (for history)
    # Don't delete delivered orders - they're needed for driver history!
    orders = Order.objects.filter(farmer=farmer).order_by('-order_date')

    # ✅ Optional: Separate for better UI
    active_orders = orders.exclude(status="Delivered")
    delivered_orders = orders.filter(status="Delivered")

    context = {
        'orders': active_orders,  # Show only active orders in main table
        'delivered_orders': delivered_orders,  # Optional: show in separate section
        'farmer': farmer,
    }

    return render(request, "farmer_order.html", context)

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

    # ✅ Only products with stock > 0
    products = Product.objects.filter(quantity__gt=0)

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

from django.http import FileResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
from .models import Order, Product, Notification


def generate_receipt(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    data = {
        'order': order,
        'amount': order.total_amount,
    }
    return render_to_pdf('receipt_pdf.html', data)


from io import BytesIO
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.http import HttpResponse


def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()

    # "ISO-8859-1" ko badal kar "utf-8" karein
    # Views.py ke andar render_to_pdf mein ye line confirm karo:
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None



from django.shortcuts import render

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

    if request.method == "POST":
        # Text fields update
        driver.name = request.POST.get('name', driver.name)
        driver.phone = request.POST.get('phone', driver.phone)
        driver.location = request.POST.get('location', driver.location)
        driver.vehicle_type = request.POST.get('vehicle_type', driver.vehicle_type)
        driver.vehicle_number = request.POST.get('vehicle_number', driver.vehicle_number)

        # Numeric fields (Empty hone par purani value rakhega)
        capacity = request.POST.get('capacity')
        if capacity:
            driver.capacity_kg = capacity

        rate = request.POST.get('rate_per_km')
        if rate:
            driver.rate_per_km = rate

        # 🛑 DATE FIELDS FIX: Khali string check karna zaroori hai
        issue_date = request.POST.get('license_issue_date')
        expiry_date = request.POST.get('license_expiry_date')

        if issue_date:  # Agar date select ki hai tabhi save karo
            driver.license_issue_date = issue_date

        if expiry_date:
            driver.license_expiry_date = expiry_date

        # Files update
        if request.FILES.get('driver_photo'):
            driver.driver_photo = request.FILES['driver_photo']
        if request.FILES.get('license_doc'):
            driver.license_doc = request.FILES['license_doc']
        if request.FILES.get('vehicle_photo'):
            driver.vehicle_photo = request.FILES['vehicle_photo']

        try:
            driver.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('driver_profile')
        except Exception as e:
            messages.error(request, f"Error saving data: {e}")

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

# Delete Single Notification
def delete_notification(request, id):
    n = get_object_or_404(Notification, id=id)
    n.delete()
    return redirect('notifications')


# Delete All Notifications
def delete_all_notification(request):
    Notification.objects.all().delete()  # REMOVE <id> from URL else error
    return redirect('notifications')

# 🔥 Retailer Orders Auto Delete Delivered
from django.shortcuts import render, redirect, get_object_or_404
from .models import Retailer, Order, Product

def retailer_products(request):
    # 1. Security Check: Ensure only retailers can access
    if request.session.get("user_type") != "retailer":
        return redirect("retailer_login")

    # 2. Get current retailer details
    retailer_name = request.session.get("name")
    retailer = get_object_or_404(Retailer, name=retailer_name)

    # 3. FIX: Removed Order.objects.filter(...).delete()
    # Data ko delete nahi karna hai taaki Driver Dashboard ki history bani rahe.

    # 4. Fetch Active Orders only
    # Hum 'Delivered' orders ko exclude kar rahe hain taaki Retailer ko sirf
    # vahi orders dikhein jo process mein hain (Pending, Accepted, Dispatched, etc.)
    orders = Order.objects.filter(retailer=retailer).exclude(status="Delivered").order_by('-order_date')

    # 5. Render the page with filtered orders
    return render(request, "retailer_products.html", {"orders": orders})

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

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Product, Order, Retailer, Farmer, Driver, Delivery, Notification, DriverNotification, \
    Sale  # Ensure Sale is imported!


# Assuming 'Sale' model has fields: product, amount, profit, quantity, status (as per your earlier code)

# ---------- PLACE ORDER ----------
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
# Ensure Sale model is imported!
from .models import Product, Order, Retailer, Farmer, Driver, Delivery, Notification, DriverNotification, Sale


# ---------- PLACE ORDER ----------
# views.py

# Ensure you have all necessary imports
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum  # Required for sales_api
from django.http import JsonResponse  # Required for sales_api
from .models import Product, Order, Retailer, Farmer, Driver, Delivery, Notification, DriverNotification, Sale


# ---------- PLACE ORzzzzzzzzDER (Updated for 95% Profit) ----------



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
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseForbidden
from .models import Order, Delivery, Product, Notification
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseForbidden
from .models import Order, Notification


@csrf_exempt
def payment_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # Razorpay कडून येणारा डेटा गोळा करा
    payment_id = request.POST.get('razorpay_payment_id')
    razorpay_order_id = request.POST.get('razorpay_order_id')
    signature = request.POST.get('razorpay_signature')

    # जर डेटा मिळत नसेल (उदा. डायरेक्ट URL ओपन केली तर), तर फेल दाखवा
    if not payment_id:
        print("Error: Razorpay payment_id not found in request.")
        return render(request, "payment_failed.html")

    # सिस्टिमला सांगा की पेमेंट झाले आहे (Verification Logic)
    # टीप: लाइव्ह मोडमध्ये सिग्नचर व्हेरिफिकेशन महत्त्वाचे असते,
    # पण सध्या तुमची ऑर्डर अपडेट करण्यासाठी आपण थेट स्टेटस 'Paid' करत आहोत.

    if order.status != "Paid":
        order.status = "Paid"

        # स्टॉक अपडेट करा
        product = order.product
        if product.quantity >= order.quantity:
            product.quantity -= order.quantity
            product.save()

        # रक्कम अपडेट करा
        total_amount = order.quantity * product.price
        order.total_amount = total_amount
        order.save()

        # शेतकरी रक्कम (९५%)
        farmer_amount = round(total_amount * 0.95, 2)

        # नोटिफिकेशन पाठवा
        Notification.objects.create(
            sender_retailer=order.retailer,
            receiver_farmer=order.farmer,
            message=f"Payment received for Order #{order.id}. Farmer amount ₹{farmer_amount}"
        )
        print(f"Order #{order.id} status updated to Paid.")

    return render(request, "payment_success.html", {"order": order})

# ------------------------
# Update Status (Farmer)
# ------------------------
from .models import Delivery
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .models import Order, Driver, Delivery, Notification


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

# views.py (Update 'mark_notification_read')


# ---------- DRIVER AUTH / DASHBOARD ----------
from django.contrib.auth import login as auth_login, logout as auth_logout

from django.contrib import messages
from .models import Driver

# views.py (driver_login)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Driver

# For Driver Login (same idea for Farmer/Retailer)
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Driver

from django.contrib.auth.hashers import check_password
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import Driver


def driver_login(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()

        if not email or not password:
            messages.error(request, "Both email and password are required")
            return redirect("driver_login")

        try:
            driver = Driver.objects.get(email=email)

            # 🔐 Check hashed password
            if not check_password(password, driver.password):
                messages.error(request, "Incorrect password")
                return redirect("driver_login")

            # 📧 Check email verified
            if not driver.email_verified:
                messages.error(request, "Please verify your email before login.")
                return redirect("driver_register")

            # ✅ Save session
            request.session['id'] = driver.id
            request.session['user_type'] = 'driver'
            request.session['name'] = driver.name
            request.session['profile_image'] = (
                driver.driver_photo.url
                if driver.driver_photo
                else '/static/images/no-image.jpg'
            )

            messages.success(request, f"Welcome {driver.name}!")
            return redirect('driver_dashboard')

        except Driver.DoesNotExist:
            messages.error(request, "Driver not found")
            return redirect("driver_login")

    return render(request, "driver_login.html")

def driver_logout(request):
    request.session.flush()
    return redirect('home')

from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Driver  # सुनिश्चित करें कि यह आपके मॉडल को import करता है


import random
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import Driver

import random
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password
from .models import Driver

import random
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from .models import Driver  # Ensure your model name is correct


def driver_register(request):
    if request.method == "POST":
        # Capture EXACT names from HTML attributes
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')  # Was missing in your HTML
        password = request.POST.get('password')

        vehicle_number = request.POST.get('vehicle_number')
        vehicle_type = request.POST.get('vehicle_type')
        capacity = request.POST.get('capacity')
        rate = request.POST.get('rate_per_km')  # Match name="rate_per_km"
        location = request.POST.get('location')

        # Files
        license_img = request.FILES.get('license_image')
        vehicle_img = request.FILES.get('vehicle_image')

        # Dates
        issue_date = request.POST.get('license_issue_date')
        expiry_date = request.POST.get('license_expiry_date')

        # Saving to Database
        driver = Driver.objects.create(
            name=name,
            email=email,
            phone=phone,
            password=make_password(password),
            vehicle_type=vehicle_type,
            vehicle_number=vehicle_number,
            capacity_kg=capacity,
            rate_per_km=rate,
            location=location,
            license_doc=license_img,
            vehicle_photo=vehicle_img,
            license_issue_date=issue_date,
            license_expiry_date=expiry_date,
            email_verified=True  # Since you verified it via JS alert
        )

        # IMPORTANT: Set session so profile isn't empty
        request.session['id'] = driver.id

        messages.success(request, "Registration successful!")
        return redirect('driver_profile')

    # This prevents the 'Returned None' error
    return render(request, "driver_register.html")





from datetime import timedelta

def verify_driver_otp(request):

    driver_id = request.session.get("verify_driver_id")

    if not driver_id:
        return redirect("driver_register")

    driver = Driver.objects.get(id=driver_id)

    if request.method == "POST":
        entered_otp = request.POST.get("otp")

        # OTP expiry 5 minutes
        if driver.otp == entered_otp and \
           timezone.now() <= driver.otp_created_at + timedelta(minutes=5):

            driver.email_verified = True
            driver.otp = None
            driver.save()

            del request.session['verify_driver_id']

            messages.success(request, "Email verified successfully.")
            return redirect("driver_login")

        else:
            messages.error(request, "Invalid or expired OTP.")

    return render(request, "verify_driver_otp.html")


from django.utils import timezone
from datetime import timedelta

def verify_driver_otp(request):
    driver_id = request.session.get('verify_driver_id')

    if not driver_id:
        return redirect('driver_register')

    driver = Driver.objects.get(id=driver_id)

    if request.method == "POST":
        entered_otp = request.POST.get('otp')

        # OTP expiry 5 minutes
        if driver.otp == entered_otp and timezone.now() <= driver.otp_created_at + timedelta(minutes=5):
            driver.email_verified = True
            driver.otp = None
            driver.save()

            messages.success(request, "Email verified successfully. Please login.")
            return redirect('driver_login')
        else:
            messages.error(request, "Invalid or expired OTP.")

    return render(request, "verify_driver_otp.html")


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

# views.py

from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Order, Driver, Delivery, Notification  # Ensure all models are imported!


# ---------------------------------------------------------------------------------
# views.py

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
            # Agar payment success ho gaya hai, toh yahan driver ko payout 'True' kar dena chahiye
            # ya yeh step ek alag admin process mein hota hai.
            # Filhaal, hum status 'Completed' rakhte hain.
            delivery.save()

        messages.success(request, f"Payment for Order #{order_id} complete.")
        return redirect('retailer_dashboard')

    messages.error(request, "Payment failed or not initiated.")
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

# views.py


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

from django.shortcuts import render
from django.db.models import Sum
from django.http import JsonResponse
from .models import Farmer, Product, Sale


# projectapp/views.py
# ================== FARMER DASHBOARD (FINAL WORKING) ==================

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum

# ================== API FOR LIVE UPDATES IN DASHBOARD ==================

from django.http import JsonResponse

# ================== API FOR LIVE UPDATES IN DASHBOARD ==================

from django.db.models import Sum

# views.py (Corrected send_driver_payment_notification)
def send_driver_payment_notification(order):
    from .models import Notification, Delivery

    delivery = Delivery.objects.filter(order=order).first()
    if not delivery: return

    driver = delivery.driver
    if not driver: return

    # ✔ 4. Driver's actual earning ko use karein, 5% commission nahi
    driver_net_earning = delivery.driver_earning or 0

    # ✔ 5. Notification send
    Notification.objects.create(
        receiver_driver=driver,
        message=f"💰 Payout requested for Order #{order.id}. Your earning: ₹{driver_net_earning:.2f}."
    )

from django.db import transaction

def place_order(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # ✅ Retailer login check
    retailer_name = request.session.get('name')
    if not retailer_name or request.session.get('user_type') != 'retailer':
        messages.error(request, "Please login as Retailer to place an order.")
        return redirect('retailer_login')

    retailer = get_object_or_404(Retailer, name=retailer_name)

    if request.method == "POST":
        # ✅ Quantity validation
        try:
            quantity = int(request.POST.get('quantity', '1'))
            if quantity <= 0:
                messages.error(request, "Quantity must be greater than zero.")
                return redirect('place_order', product_id=product.id)
        except ValueError:
            messages.error(request, "Invalid quantity.")
            return redirect('place_order', product_id=product.id)

        # ✅ Stock check
        if product.quantity < quantity:
            messages.error(request, "Insufficient stock available.")
            return redirect('place_order', product_id=product.id)

        contact = request.POST.get('contact', '').strip()
        address = request.POST.get('address', '').strip()

        if not contact or not address:
            messages.error(request, "Please provide address and contact.")
            return redirect('place_order', product_id=product.id)

        # ✅ Price calculation
        unit_price = product.price
        total_amount = unit_price * quantity

        COMMISSION_RATE = 0.05
        calculated_profit = total_amount * (1 - COMMISSION_RATE)

        # 🔥🔥 ATOMIC BLOCK (MOST IMPORTANT)
        with transaction.atomic():

            # ✅ Create Order
            order = Order.objects.create(
                product=product,
                quantity=quantity,
                retailer=retailer,
                contact=contact,
                address=address,
                farmer=product.farmer,
                status='Pending'
            )

            # ✅ Create Sale
            Sale.objects.create(
                product=product,
                amount=total_amount,
                profit=calculated_profit,
                quantity=quantity,
                status='Pending'
            )

            # ✅ REDUCE STOCK
            product.quantity -= quantity

            # ✅ AUTO DELETE WHEN STOCK 0
            if product.quantity <= 0:
                product.delete()
            else:
                product.save()

        messages.success(
            request,
            f"Order placed successfully! Total amount: ₹{total_amount:.2f}"
        )

        return redirect('payment_page', order_id=order.id)

    return render(request, "place_order.html", {"product": product})


# ================== API FOR LIVE UPDATES IN DASHBOARD ==================

# B. sales_api (To fetch all data for the dashboard)

def sales_api(request):
    farmer_name = request.session.get("name")
    farmer = get_object_or_404(Farmer, name=farmer_name)

    # Calculate Totals
    # Summing 'amount' for Total Sales (100% value)
    total_sales = Sale.objects.filter(product__farmer=farmer).aggregate(total=Sum("amount"))["total"] or 0
    # Summing 'profit' for Total Profit (95% net income)
    total_profit = Sale.objects.filter(product__farmer=farmer).aggregate(total=Sum("profit"))["total"] or 0
    total_products = Product.objects.filter(farmer=farmer).count()

    # Get Recent Sales
    last_sales = Sale.objects.filter(product__farmer=farmer).order_by("-date")[:5]

    sales_data = [{
        "product": sale.product.product,
        "amount": sale.amount,
        "profit": sale.profit,
        "date": sale.date.strftime("%d-%m-%Y %H:%M")
    } for sale in last_sales]

    # Combined Data to send back
    data = {
        "totals": {
            "total_sales": total_sales,
            "total_profit": total_profit,
            "total_products": total_products
        },
        "recent_sales": sales_data
    }

    return JsonResponse(data)

def farmer_dashboard(request):

    if request.session.get("user_type") != "farmer":
        return redirect("farmer_login")

    farmer = get_object_or_404(Farmer, name=request.session.get("name"))

    total_sales = Sale.objects.filter(
        product__farmer=farmer
    ).aggregate(total=Sum("amount"))["total"] or 0

    total_profit = Sale.objects.filter(
        product__farmer=farmer
    ).aggregate(total=Sum("profit"))["total"] or 0

    total_products = Product.objects.filter(farmer=farmer).count()

    recent_sales = Sale.objects.filter(
        product__farmer=farmer
    ).order_by("-date")[:5]

    pending_sales = Sale.objects.filter(
        product__farmer=farmer,
        status="Pending"
    )

    return render(request, "farmer_dashboard.html", {
        "farmer": farmer,
        "total_sales": total_sales,
        "total_products": total_products,
        "total_profit": total_profit,
        "recent_sales": recent_sales,
        "pending_sales": pending_sales
    })

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count, Sum
from .models import Retailer, Order  # Ensure Retailer and Order models are imported!
from django.utils import timezone

#########################################################################################333


# views.py (Only the modified/driver-related functions are shown)

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Q
from datetime import timedelta
from django.utils import timezone
from django.contrib import messages
# Ensure all required models are imported:
from .models import Order, Driver, Delivery, Notification, Retailer, Farmer
from django.views.decorators.http import require_POST


# --- CORE DRIVER LOGIC FIXES ---

from django.utils import timezone
from .models import Delivery, Driver, Notification

# ----------------------------------------------------------------------

# --- DRIVER DASHBOARD VIEW (Data calculation is correct) ---

from django.shortcuts import render, redirect
from django.db.models import Sum
# --- NOTIFICATION FIX (For click error) ---

def mark_notification_read(request, nid):
    user_type = request.session.get('user_type')
    name = request.session.get('name')
    n = None

    # 1. Note object find karne ka logic (as before)
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

    # 3. 🎯 Redirection Logic with robust error handling (FIXED)
    if user_type in ["driver", "farmer", "retailer"] and ("Order #" in n.message):
        try:
            # Order ID extraction
            parts = n.message.split('Order #')
            if len(parts) > 1:
                # Extracts the ID number, cleans up potential trailing characters, and converts to int
                order_id_str = parts[1].split()[0].replace('.', '').replace(',', '')
                order_id = int(order_id_str)
                return redirect("order_detail", order_id=order_id)
        except Exception:
            # If parsing fails, fall through to default redirect
            pass

            # 4. Default redirect
    return redirect("notifications")


# ----------------------------------------------------------------------

# --- DELIVERY STATUS ACTION VIEWS (FIXED Action buttons logic) ---

@require_POST
def driver_mark_picked(request, delivery_id):
    delivery = get_object_or_404(Delivery, id=delivery_id)
    order = delivery.order

    if delivery.status == 'assigned':
        delivery.status = 'picked'
        delivery.picked_at = timezone.now()
        delivery.save()

        order.status = "Picked"
        order.save()

        messages.success(request, f"Order #{order.id} is picked and is now in transit.")
    else:
        messages.warning(request, f"Cannot mark picked. Current status: {delivery.status}")

    # ✅ Use the CORRECT URL name from your urls.py
    return redirect('driver_deliveries')  # OR whatever name you have

from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from .models import Delivery

from django.utils import timezone

def driver_assigned_deliveries(request):
    driver_id = request.session.get('id')
    if not driver_id:
        return redirect('driver_login')

    driver = get_object_or_404(Driver, id=driver_id)

    # Active deliveries: Assigned or Picked
    active_deliveries = Delivery.objects.filter(
        driver=driver
    ).exclude(
        Q(status__iexact='delivered') | Q(status__iexact='canceled')
    ).select_related(
        'order',
        'order__product',
        'order__retailer',
        'order__farmer'
    ).order_by('-assigned_at')  # ✅ Ordering add kiya

    context = {
        'deliveries': active_deliveries,
        'driver': driver,
    }
    return render(request, "driver_assigned_deliveries.html", context)

####################################################################################################333


from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db.models import Sum
from django.db import transaction
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages

def retailer_dashboard(request):
    retailer_name = request.session.get('name')
    if not retailer_name or request.session.get('user_type') != 'retailer':
        return redirect('retailer_login')

    retailer = get_object_or_404(Retailer, name=retailer_name)

    # ✅ Total Orders
    total_orders = Order.objects.filter(retailer=retailer).count()

    # ✅ Delivered / Completed Orders
    completed_statuses = ['Delivered', 'Completed']

    completed_orders = Order.objects.filter(
        retailer=retailer,
        status__in=completed_statuses
    )

    # ✅ Total Amount Spent
    total_spent = 0
    for order in completed_orders:
        amount_to_add = order.total_amount

        if amount_to_add is None or amount_to_add == 0:
            amount_to_add = order.quantity * order.product.price

        total_spent += amount_to_add

    # ✅ Pending Orders
    pending_statuses = [
        'Pending', 'Paid', 'Accepted', 'Packed',
        'Dispatched', 'Driver Assigned', 'Picked',
        'Assigned to Driver'
    ]

    pending_orders = Order.objects.filter(
        retailer=retailer,
        status__in=pending_statuses
    ).count()

    # ✅ Recent Orders
    recent_orders = Order.objects.filter(
        retailer=retailer
    ).order_by('-order_date')[:5]

    for order in recent_orders:
        order.calculated_amount = (
            order.total_amount if order.total_amount is not None
            else order.quantity * order.product.price
        )

    # 🔔 ✅ NEW: Notifications for Retailer
    notifications = Notification.objects.filter(
        receiver_retailer=retailer,
        is_read=False
    ).order_by('-timestamp')

    context = {
        'retailer': retailer,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'total_spent': f"{total_spent:.2f}",
        'recent_orders': recent_orders,
        'notifications': notifications,   # ✅ Added
    }

    return render(request, "retailer_dashboard.html", context)




# --- DRIVER VIEWS ---

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from .models import Driver, Delivery

from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404

from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404

from django.db.models import Sum


def driver_dashboard(request):
    driver_id = request.session.get("id")
    if not driver_id:
        return redirect("driver_login")

    driver = get_object_or_404(Driver, id=driver_id)

    # Get ALL deliveries
    all_deliveries = Delivery.objects.filter(driver=driver).select_related(
        'order', 'order__retailer', 'order__farmer'
    )

    # Separate manually
    delivered = []
    pending = []
    total = 0

    for d in all_deliveries:
        if d.status.lower() == "delivered":
            delivered.append(d)
            if d.driver_earning:
                total += float(d.driver_earning)
        elif d.status.lower() in ["assigned", "picked"]:
            pending.append(d)

    context = {
        "driver": driver,
        "total_earnings": round(total, 2),
        "delivery_history": delivered,
        "pending_deliveries": pending,
        "total_deliveries": len(delivered),
    }

    return render(request, "driver_dashboard.html", context)

from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.contrib import messages
from .models import Delivery

from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

@require_POST
def driver_mark_delivered(request, delivery_id):
    delivery = get_object_or_404(Delivery, id=delivery_id)
    order = delivery.order

    # Status check
    if delivery.status.lower() != "picked":
        messages.warning(request, f"Cannot mark delivered. Current status: {delivery.status}")
        return redirect("driver_assigned_deliveries")

    # Calculation - Float ensure karein
    order_total = float(order.quantity) * float(order.product.price)
    delivery.driver_earning = order_total * 0.05

    # 🚨 Database mein update
    delivery.status = "delivered"  # lowercase 'd'
    delivery.delivered_at = timezone.now()
    delivery.save()

    # Order table update
    order.status = "Delivered"
    order.save()

    # Driver availability
    driver = delivery.driver
    driver.is_available = True
    driver.save()

    messages.success(request, f"Order #{order.id} successfully delivered!")
    return redirect("driver_dashboard")

# --- ADMIN/FARMER VIEWS ---

def update_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    drivers = Driver.objects.filter(is_available=True)

    if request.method == "POST":
        new_status = request.POST.get("status")
        driver_id = request.POST.get("driver")

        order.status = new_status

        if driver_id:
            driver = get_object_or_404(Driver, id=driver_id)
            order.driver = driver
            order.status = "Driver Assigned"
            order.save()

            # ✅ FIX: Check if delivery exists first
            existing_delivery = Delivery.objects.filter(order=order).first()

            if existing_delivery:
                # Update karein agar already exists
                existing_delivery.driver = driver
                existing_delivery.status = "assigned"
                existing_delivery.assigned_at = timezone.now()
                existing_delivery.save()
            else:
                # Naya banayein agar nahi hai
                Delivery.objects.create(
                    order=order,
                    driver=driver,
                    status="assigned",
                    assigned_at=timezone.now()
                )

            driver.is_available = False
            driver.save()

            # Notifications...
            Notification.objects.create(receiver_driver=driver, message=f"You are assigned Order #{order.id}")
            Notification.objects.create(receiver_retailer=order.retailer,
                                        message=f"Driver {driver.name} assigned for Order #{order.id}")
            Notification.objects.create(receiver_farmer=order.farmer,
                                        message=f"You assigned driver {driver.name} for Order #{order.id}")
        else:
            order.save()

        # Status-based notifications (rest of your code remains same)
        if new_status == "Accepted":
            Notification.objects.create(receiver_retailer=order.retailer,
                                        message=f"Order #{order.id} accepted by farmer")
        # ... etc

        return redirect("farmer_order")

    return render(request, "update_status.html", {"order": order, "drivers": drivers})


from django.utils import timezone
from .models import Delivery, Driver

def assign_driver_to_order(order):
    driver = Driver.objects.filter(is_available=True).first()
    if not driver:
        return None

    DELIVERY_CHARGE = 50   # tum chaaho to dynamic bana sakte ho

    delivery = Delivery.objects.create(
        order=order,
        driver=driver,
        delivery_charge=DELIVERY_CHARGE,
        driver_earning=0,
        status="assigned",
        assigned_at=timezone.now()
    )

    driver.is_available = False
    driver.save()

    return delivery




# The rest of the views (place_order, driver_toggle_availability, complete_order_payment, update_delivery_status, auto_assign_driver)
# are generally okay, but driver_mark_delivered was the main one needing earning and status fix.


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import SampleRequest

# -------------------------------
# Retailer: Request Sample
# -------------------------------
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Retailer, Product, SampleRequest

def request_sample(request, product_id):
    # ✅ Get retailer id from session
    retailer_id = request.session.get("id")
    if not retailer_id:
        messages.error(request, "Please login first")
        return redirect("retailer_login")

    retailer = get_object_or_404(Retailer, id=retailer_id)
    product = get_object_or_404(Product, id=product_id)

    # ✅ Create sample request
    SampleRequest.objects.create(
        product=product,
        retailer=retailer,
        farmer=product.farmer,
        quantity=2  # default sample quantity
    )

    messages.success(request, f"Sample request for '{product.product}' sent successfully!")
    return redirect("retailer_dashboard")
# -------------------------------
# Farmer: View Sample Requests
# -------------------------------
from django.shortcuts import get_object_or_404, render
from .models import Farmer, SampleRequest
from django.contrib import messages

def farmer_sample_requests(request):

    # ✅ STRICT CHECK
    if request.session.get("user_type") != "farmer":
        return redirect("farmer_login")

    farmer_id = request.session.get("id")
    if not farmer_id:
        return redirect("farmer_login")

    farmer = Farmer.objects.get(id=farmer_id)

    samples = SampleRequest.objects.filter(farmer=farmer)

    # ✅ NO EXTRA FILTER – DIRECT
    available_drivers = Driver.objects.all()

    print("DEBUG DRIVERS:", available_drivers)  # 👈 MUST PRINT

    return render(request, "farmer_sample_requests.html", {
        "samples": samples,
        "available_drivers": available_drivers
    })

# -------------------------------
# Farmer: Approve / Reject Sample
# -------------------------------
def approve_sample(request, id):
    sample = get_object_or_404(SampleRequest, id=id)
    sample.status = "approved"
    sample.save()
    messages.success(request, "Sample request approved!")
    return redirect("farmer_sample_requests")


def reject_sample(request, id):
    sample = get_object_or_404(SampleRequest, id=id)
    sample.status = "rejected"
    sample.save()
    messages.success(request, "Sample request rejected!")
    return redirect("farmer_sample_requests")


# -------------------------------
# Driver: Assign Sample & Deliver
# -------------------------------
def assign_sample_driver(request, id):

    # ✅ Only FARMER can assign
    if request.session.get("user_type") != "farmer":
        return redirect("farmer_login")

    if request.method == "POST":

        driver_id = request.POST.get("driver_id")
        if not driver_id:
            messages.error(request, "Please select a driver")
            return redirect("farmer_sample_requests")

        sample = get_object_or_404(SampleRequest, id=id)
        driver = get_object_or_404(Driver, id=driver_id)

        sample.driver = driver
        sample.status = "picked"
        sample.save()

        messages.success(request, f"Driver {driver.name} assigned successfully")

    return redirect("farmer_sample_requests")

def driver_mark_sample_picked(request, id):
    if request.session.get("user_type") != "driver":
        return redirect("driver_login")

    sample = get_object_or_404(SampleRequest, id=id)

    sample.status = "picked"
    sample.save()

    messages.success(request, "Sample picked successfully")
    return redirect("driver_sample_deliveries")

def deliver_sample_complete(request, id):
    if request.session.get("user_type") != "driver":
        return redirect("driver_login")

    sample = get_object_or_404(SampleRequest, id=id)

    sample.status = "delivered"
    sample.save()

    messages.success(request, "Sample delivered successfully")

    # 🔥 AFTER DELIVERY → RETAILER CAN REVIEW
    return redirect("driver_sample_deliveries")
# projectapp/views.py
from django.shortcuts import render, get_object_or_404
from .models import SampleRequest, Driver

def driver_sample_deliveries(request):

    # ✅ Only driver allowed
    if request.session.get("user_type") != "driver":
        return redirect("driver_login")

    driver_id = request.session.get("id")
    if not driver_id:
        return redirect("driver_login")

    driver = Driver.objects.get(id=driver_id)

    # 🔥 IMPORTANT FILTER
    samples = SampleRequest.objects.filter(
        driver=driver
    ).order_by("-id")

    return render(request, "driver_sample_deliveries.html", {
        "samples": samples
    })
# -------------------------------
# Retailer: Rate & Review Sample
# -------------------------------
# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import SampleRequest, Retailer

# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import SampleRequest, Retailer

def rate_sample(request, id):
    # ✅ Only retailer
    if request.session.get("user_type") != "retailer":
        messages.error(request, "Please login first")
        return redirect("retailer_login")

    retailer_id = request.session.get("id")
    retailer = get_object_or_404(Retailer, id=retailer_id)

    sample = get_object_or_404(SampleRequest, id=id, retailer=retailer)

    if request.method == "POST":
        rating = int(request.POST.get("rating"))
        review = request.POST.get("review")
        sample.rating = rating
        sample.review = review
        sample.save()
        messages.success(request, "Thank you for your review!")
        return redirect("retailer_dashboard")  # ✅ changed

    return render(request, "rate_sample.html", {"sample": sample})

def retailer_samples(request):
    if request.session.get('user_type') != 'retailer':
        return redirect('retailer_login')

    retailer_id = request.session.get('id')
    retailer = Retailer.objects.get(id=retailer_id)

    # Delivered samples
    samples = SampleRequest.objects.filter(
        retailer=retailer,
        status='delivered'
    )

    return render(request, "retailer_samples.html", {"samples": samples})

from django.shortcuts import render
from .models import SampleRequest  # jo model me reviews store hote hai

def all_sample_reviews(request):
    # Show all submitted reviews
    reviews = SampleRequest.objects.select_related('retailer').all().order_by('-id')
    return render(request, "all_sample_reviews.html", {"reviews": reviews})


from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Bid, Order, Notification
from django.contrib import messages


# 1. Retailer jab offer bhejta hai
from django.contrib.auth.decorators import login_required

from django.contrib.auth.decorators import login_required


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Product, Bid

def place_bid(request, product_id):

    retailer_id = request.session.get("id")
    user_type = request.session.get("user_type")

    if not retailer_id or user_type != "retailer":
        messages.error(request, "Please login as Retailer")
        return redirect("retailer_login")

    product = get_object_or_404(Product, id=product_id)
    retailer = get_object_or_404(Retailer, id=retailer_id)

    if request.method == "POST":
        proposed_price = request.POST.get("proposed_price")
        quantity = request.POST.get("quantity")

        Bid.objects.create(
            product=product,
            retailer=retailer,
            farmer=product.farmer,
            proposed_price=proposed_price,
            quantity=quantity,
            status="Pending"
        )

        messages.success(request, "Offer sent to Farmer")
        return redirect("browse_products")


# 2. Farmer dashboard jahan sari bids dikhengi
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Bid


def manage_bids(request):

    farmer_id = request.session.get("id")
    user_type = request.session.get("user_type")

    if not farmer_id or user_type != "farmer":
        messages.error(request, "Only farmers allowed")
        return redirect("farmer_login")

    farmer = get_object_or_404(Farmer, id=farmer_id)

    bids = Bid.objects.filter(
        farmer=farmer,
        status="Pending"
    ).order_by("-created_at")

    return render(request, "farmer_bids.html", {"bids": bids})

# 3. Farmer jab offer Accept karta hai
from django.urls import reverse

def accept_bid(request, bid_id):

    farmer_id = request.session.get("id")
    user_type = request.session.get("user_type")

    if not farmer_id or user_type != "farmer":
        messages.error(request, "Unauthorized")
        return redirect("farmer_login")

    bid = get_object_or_404(Bid, id=bid_id, farmer_id=farmer_id)

    bid.status = "Accepted"
    bid.save()

    # ✅ Create Order
    order = Order.objects.create(
        product=bid.product,
        retailer=bid.retailer,
        farmer=bid.farmer,
        quantity=bid.quantity,
        status="Pending Payment"
    )

    # ✅ Generate correct payment URL dynamically
    payment_url = reverse('payment_page', args=[order.id])

    # ✅ Create Notification with correct URL
    Notification.objects.create(
        receiver_retailer=bid.retailer,
        sender_farmer=bid.farmer,
        message=f"Your offer for {bid.product.product} has been accepted!",
        link=payment_url
    )

    messages.success(request, "Offer accepted. Retailer notified for payment.")
    return redirect("manage_bids")

# 4. Farmer jab offer Reject karta hai (Yahan error aa raha tha)
def reject_bid(request, bid_id):

    farmer_id = request.session.get("id")
    user_type = request.session.get("user_type")

    if not farmer_id or user_type != "farmer":
        messages.error(request, "Unauthorized")
        return redirect("farmer_login")

    bid = get_object_or_404(Bid, id=bid_id, farmer_id=farmer_id)

    bid.status = "Rejected"
    bid.save()

    Notification.objects.create(
        receiver_retailer=bid.retailer,
        message=f"Farmer {bid.farmer.name} rejected your offer for {bid.product.product}"
    )

    messages.warning(request, "Bid rejected")
    return redirect("manage_bids")


def pay_bid(request, bid_id):

    retailer_name = request.session.get('name')
    if not retailer_name or request.session.get('user_type') != 'retailer':
        return redirect('retailer_login')

    retailer = get_object_or_404(Retailer, name=retailer_name)
    bid = get_object_or_404(Bid, id=bid_id, retailer=retailer, status="Accepted")

    total_amount = float(bid.proposed_price) * bid.quantity

    # ✅ Create order after payment
    order = Order.objects.create(
        product=bid.product,
        farmer=bid.farmer,
        retailer=bid.retailer,
        quantity=bid.quantity,
        total_amount=total_amount,
        status="Paid"
    )

    # Optional: mark bid completed
    bid.status = "Completed"
    bid.save()

    messages.success(request, f"Payment successful! Order #{order.id} created.")
    return redirect("retailer_dashboard")

