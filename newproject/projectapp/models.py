from django.db import models
from django.core.files.base import ContentFile
from io import BytesIO
from PIL import Image, UnidentifiedImageError

# ------------------------
# Original Farmer model
# ------------------------
from django.db import models
from django.contrib.auth.models import AbstractUser

# ✅ Custom User
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

from django.db import models
from PIL import Image
from django.utils import timezone
from datetime import timedelta  # Iski bhi zaroorat padegi 'is_fresh' ke liye

class Farmer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    password = models.CharField(max_length=100)
    contact = models.CharField(max_length=20)
    address = models.TextField()
    gender = models.CharField(max_length=10)
    first_login = models.BooleanField(default=True)
    profile_image = models.ImageField(upload_to='profiles/', default='profiles/default.jpg')

    def __str__(self):
        return self.name

class Retailer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)

    contact = models.CharField(max_length=15)
    address = models.TextField()

    city = models.CharField(max_length=50, blank=True, null=True)
    pincode = models.CharField(max_length=6, blank=True, null=True)

    gender = models.CharField(max_length=10)

    shop_number = models.CharField(max_length=50)   # ✔ New field
    gst_number = models.CharField(max_length=15)    # ✔ New field

    first_login = models.BooleanField(default=True)
    profile_image = models.ImageField(upload_to='profiles/', default='profiles/default.jpg')

    email_verified = models.BooleanField(default=False)
    email_otp = models.CharField(max_length=6, blank=True, null=True)


def __str__(self):
        return self.name


# Product model (unchanged)
# ------------------------
class Product(models.Model):
    product = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    price = models.FloatField()
    quantity = models.IntegerField()
    location = models.CharField(max_length=50)
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    farmer = models.ForeignKey('Farmer', on_delete=models.CASCADE, related_name='products')

    @property
    def is_fresh(self):
        from django.utils import timezone
        from datetime import timedelta
        return self.created_at >= timezone.now() - timedelta(days=3)

    def __str__(self):
        return self.product

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.image:
            return

        try:
            img_path = self.image.path
        except Exception:
            return

        MAX_SIZE = (800, 800)

        try:
            img = Image.open(img_path)
        except UnidentifiedImageError:
            return

        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=85, optimize=True)
        buffer.seek(0)

        with open(img_path, 'wb') as f:
            f.write(buffer.read())
        buffer.close()

# ------------------------
# Notification model (added for Farmer/Retailer)
# ------------------------
from django.db import models
from .models import Farmer, Retailer

# models.py
from django.db import models
from django.utils import timezone


class Notification(models.Model):
    sender_farmer = models.ForeignKey('Farmer', on_delete=models.SET_NULL, null=True, blank=True)
    sender_retailer = models.ForeignKey('Retailer', on_delete=models.SET_NULL, null=True, blank=True)
    receiver_farmer = models.ForeignKey('Farmer', on_delete=models.CASCADE, null=True, blank=True,
                                        related_name='notifications_received')
    receiver_retailer = models.ForeignKey('Retailer', on_delete=models.CASCADE, null=True, blank=True,
                                          related_name='notifications_received')
    receiver_driver = models.ForeignKey('Driver', on_delete=models.CASCADE, null=True, blank=True,
                                        related_name='notifications_received')

    message = models.TextField()
    link = models.CharField(max_length=500, null=True, blank=True)  # NEW: direct link
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.message[:30]}..."



# Order model (unchanged)
# ------------------------

# ------------------------
# ChatMessage and ContactMessage models unchanged
# ------------------------
from django.db import models
from django.conf import settings

# import your Farmer/Retailer models as appropriate:
# from users.models import Farmer, Retailer

from django.db import models

# Chat messages (linked to an Order)
from django.db import models


class ChatMessage(models.Model):
    order = models.ForeignKey("Order", on_delete=models.CASCADE)

    # Either sender is a farmer or a retailer
    sender_farmer = models.ForeignKey("Farmer", null=True, blank=True, on_delete=models.CASCADE)
    sender_retailer = models.ForeignKey("Retailer", null=True, blank=True, on_delete=models.CASCADE)

    message = models.TextField(blank=True)
    image = models.ImageField(upload_to="chat_images/", blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    seen = models.BooleanField(default=False)

    def __str__(self):
        if self.sender_farmer:
            return f"{self.sender_farmer.name}: {self.message}"
        if self.sender_retailer:
            return f"{self.sender_retailer.name}: {self.message}"
        return "Unknown sender"


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name} ({self.email})"


# projectapp/models.py
from django.db import models
from django.utils import timezone

# --- existing Farmer, Retailer, Product, Order, ... stay above ---

# models.py में नया, मर्ज किया गया Driver मॉडल

from django.db import models
from django.contrib.auth.hashers import make_password
from django.utils import timezone


class Driver(models.Model):
    VEHICLE_CHOICES = [
        ('bike', 'Bike'),
        ('auto', 'Auto'),
        ('tempo', 'Tempo'),
        ('pickup', 'Pickup'),
        ('truck', 'Truck'),
    ]

    # --- Basic Fields ---
    name = models.CharField(max_length=120)
    email = models.EmailField(unique=True)
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    email_verified = models.BooleanField(default=False)

    phone = models.CharField(max_length=20, blank=True, null=True)
    password = models.CharField(max_length=128)

    vehicle_type = models.CharField(
        max_length=20,
        choices=VEHICLE_CHOICES,
        default='tempo'
    )

    vehicle_number = models.CharField(max_length=50, blank=True, null=True)
    capacity_kg = models.IntegerField(default=1000)
    rate_per_km = models.FloatField(default=12.0)
    is_available = models.BooleanField(default=False)
    location = models.CharField(max_length=150, blank=True, null=True)

    driver_photo = models.ImageField(
        upload_to='drivers/',
        blank=True,
        null=True
    )

    license_doc = models.FileField(
        upload_to='drivers/docs/',
        blank=True,
        null=True
    )

    vehicle_photo = models.ImageField(
        upload_to='drivers/vehicle_photos/',
        blank=True,
        null=True
    )

    phone_verified = models.BooleanField(default=False)
    license_issue_date = models.DateField(blank=True, null=True)
    license_expiry_date = models.DateField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.name} ({self.vehicle_type})"


# पुराने DriverProfile मॉडल को हटा दें
# class DriverProfile(models.Model): ... को हटा दें

# projectapp/models.py

from django.db import models
from django.utils import timezone

class Delivery(models.Model):
    STATUS_CHOICES = [
        ('assigned', 'Assigned'),
        ('picked', 'Picked'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('canceled', 'Canceled'),
    ]

    order = models.ForeignKey('Order', on_delete=models.PROTECT, related_name='deliveries')
    driver = models.ForeignKey('Driver', on_delete=models.SET_NULL, null=True, blank=True, related_name='deliveries')

    distance_km = models.FloatField(default=0.0)
    delivery_charge = models.FloatField(default=0.0)  # retailer pays
    driver_earning = models.FloatField(default=0.0)  # earning after commission
    is_paid_out = models.BooleanField(default=False)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='assigned')
    assigned_at = models.DateTimeField(auto_now_add=True)
    picked_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Delivery #{self.id} - Order {self.order.id} - {self.status}"

from django.db import models

from django.db import models

class SampleRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('picked', 'Picked'),
        ('delivered', 'Delivered'),
    ]

    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    farmer = models.ForeignKey('Farmer', on_delete=models.CASCADE)
    retailer = models.ForeignKey('Retailer', on_delete=models.CASCADE)
    driver = models.ForeignKey('Driver', on_delete=models.SET_NULL, null=True, blank=True)

    quantity = models.FloatField(default=2, help_text="Sample quantity in kg")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    rating = models.IntegerField(null=True, blank=True)
    review = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Sample #{self.id} - {self.product.product}"

from django.db import models
from django.contrib.auth import get_user_model

# Assuming you have SampleRequest, Retailer models already
class RetailerSampleReview(models.Model):
    sample = models.ForeignKey('SampleRequest', on_delete=models.CASCADE)
    retailer = models.ForeignKey('Retailer', on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField()  # 1-5 stars
    review = models.TextField(blank=True, null=True)
    reviewed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('sample', 'retailer')  # prevents multiple reviews for same sample

    def __str__(self):
        return f"{self.retailer.name} - {self.sample.product.product} - {self.rating}"
# models.py
from django.db import models


class DriverNotification(models.Model):
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notif to {self.driver.name} - {self.message[:30]}"


from django.db import models

class Order(models.Model):

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Packed', 'Packed'),
        ('Dispatched', 'Dispatched'),
        ('Delivered', 'Delivered'),
        ('Paid', 'Paid'),
    ]

    product = models.ForeignKey('Product', on_delete=models.PROTECT, related_name='orders')
    farmer = models.ForeignKey('Farmer', on_delete=models.CASCADE, related_name='orders', default=1)
    retailer = models.ForeignKey('Retailer', on_delete=models.CASCADE, related_name='orders')
    quantity = models.IntegerField(default=1)
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Pending')
    address = models.TextField(blank=True, null=True)
    contact = models.CharField(max_length=20, blank=True, null=True)
    current_lat = models.FloatField(null=True, blank=True)
    current_lng = models.FloatField(null=True, blank=True)
    driver = models.ForeignKey('Driver', on_delete=models.SET_NULL, null=True, blank=True)

    total_amount = models.FloatField(default=0.0)

    farmer_paid = models.BooleanField(default=False)  # ✅ ADD THIS

    def __str__(self):
        return f"Order#{self.id} - {self.product.product} ({self.retailer.name})"

# models.py (only the Sale model part shown)
from django.db import models

class Sale(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE)   # FK to Product
    amount = models.FloatField()      # total money received for this sale
    profit = models.FloatField()      # profit amount for farmer (or net profit)
    date = models.DateTimeField(auto_now_add=True)
    quantity = models.FloatField(default=1)
    status = models.CharField(max_length=50, default='Pending')

    def __str__(self):
        # note: Product model field that stores title is called product (string)
        product_title = getattr(self.product, "product", "Unknown product")
        return f"{product_title} - {self.amount}"


# models.py
class Bid(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
    ]
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    retailer = models.ForeignKey(Retailer, on_delete=models.CASCADE) # Aapke model ke hisaab se use karein
    farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE)
    proposed_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Bid by {self.retailer.name} for {self.product.product}"