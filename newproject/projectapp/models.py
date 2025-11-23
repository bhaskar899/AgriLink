from django.db import models

from django.db import models

# models.py

class Farmer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    password = models.CharField(max_length=100)
    contact = models.CharField(max_length=20)
    address = models.TextField()
    gender = models.CharField(max_length=10)
    first_login = models.BooleanField(default=True)
    profile_image = models.ImageField(upload_to='profiles/', default='profiles/default.jpg')

    def _str_(self):
        return self.name


class Retailer(models.Model):
    name = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    contact = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    first_login = models.BooleanField(default=True)
    profile_image = models.ImageField(upload_to='profiles/', default='profiles/default.jpg')

    def _str_(self):
        return self.name
# ... (rest of models like Product, Order, etc. are omitted for brevity, but keep them as you had)
from django.db import models
from django.core.files.base import ContentFile
from io import BytesIO
from PIL import Image, UnidentifiedImageError
import os

class Product(models.Model):
    product = models.CharField(max_length=100)
    description = models.TextField()
    price = models.FloatField()
    quantity = models.IntegerField()
    location = models.CharField(max_length=50)
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    farmer = models.ForeignKey('Farmer', on_delete=models.CASCADE, related_name='products')

    def __str__(self):
        return self.product

    def save(self, *args, **kwargs):
        """
        Override save to resize/optimize images.
        - Keeps images under max dimension (800x800).
        - Converts PNG/WebP to JPEG to reduce size (keeps extension .jpg).
        - Keeps existing behavior if no image uploaded.
        """
        super().save(*args, **kwargs)  # first save so self.image.path exists if uploaded

        if not self.image:
            return

        try:
            img_path = self.image.path
        except ValueError:
            # storage might be remote or image not on disk
            return
        except Exception:
            return

        MAX_SIZE = (800, 800)  # max width/height

        try:
            img = Image.open(img_path)
        except UnidentifiedImageError:
            # corrupted image — silently ignore (or log)
            return

        # Only resize if bigger
        # if img.width > MAX_SIZE[0] or img.height > MAX_SIZE[1]:
        #     img.thumbnail(MAX_SIZE, Image.ANTIALIAS)

        # Convert mode if needed
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # Save optimized version back to disk
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=85, optimize=True)
        buffer.seek(0)

        # Overwrite the file on disk (safe)
        with open(img_path, 'wb') as f:
            f.write(buffer.read())

        buffer.close()

class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Packed', 'Packed'),
        ('Dispatched', 'Dispatched'),
        ('Delivered', 'Delivered'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='orders')
    farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE, related_name='orders')
    retailer = models.ForeignKey(Retailer, on_delete=models.CASCADE, related_name='orders')
    quantity = models.IntegerField(default=1)
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Pending')

    # ✅ Add these new fields:
    address = models.TextField(blank=True, null=True)
    contact = models.CharField(max_length=20, blank=True, null=True)

    # optional current location for tracking
    current_lat = models.FloatField(null=True, blank=True)
    current_lng = models.FloatField(null=True, blank=True)

    def _str_(self):
        return f"Order#{self.id} - {self.product.product} ({self.retailer.name})"

class ChatMessage(models.Model):
    # either sender_farmer OR sender_retailer will be set
    sender_farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE, null=True, blank=True, related_name='sent_msgs')
    receiver_farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE, null=True, blank=True, related_name='received_msgs_farmer')
    sender_retailer = models.ForeignKey(Retailer, on_delete=models.CASCADE, null=True, blank=True, related_name='sent_msgs_retailer')
    receiver_retailer = models.ForeignKey(Retailer, on_delete=models.CASCADE, null=True, blank=True, related_name='received_msgs_retailer')

    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        sender = self.sender_farmer or self.sender_retailer
        return f"Msg from {sender} at {self.timestamp}"

class Notification(models.Model):
    # user_type: 'farmer' or 'retailer'
    user_type = models.CharField(max_length=10)
    user_name = models.CharField(max_length=100)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def _str_(self):
        return f"{self.user_name} - {self.message[:30]}"


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        return f"Message from {self.name} ({self.email})"