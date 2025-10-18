from django.db import models

# Farmer Model
class Farmer(models.Model):
    name = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=50)
    contact = models.CharField(max_length=15)
    address = models.TextField()
    gender = models.CharField(max_length=10)

    def _str_(self):
        return self.name


# Retailer Model
class Retailer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=50)
    contact = models.CharField(max_length=15)
    address = models.TextField()
    gender = models.CharField(max_length=10)

    def _str_(self):
        return self.name


# Product Model
class Product(models.Model):
    product = models.CharField(max_length=100)
    description = models.TextField()
    price = models.FloatField()
    quantity = models.IntegerField()
    location = models.CharField(max_length=50)
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE)

    def _str_(self):
        return self.product


# Order Model
class Order(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE)
    retailer = models.ForeignKey(Retailer, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=30, default="Pending")

    # Tracking ke liye location fields
    current_lat = models.FloatField(null=True, blank=True)
    current_lng = models.FloatField(null=True, blank=True)

    def _str_(self):
        return f"{self.product.product} - {self.retailer.name}"


# ✅ ChatMessage ko alag class banao (nested nahi)
class ChatMessage(models.Model):
    sender_farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE, null=True, blank=True,
                                       related_name='sent_messages_farmer')
    receiver_retailer = models.ForeignKey(Retailer, on_delete=models.CASCADE, null=True, blank=True,
                                          related_name='received_messages_retailer')
    sender_retailer = models.ForeignKey(Retailer, on_delete=models.CASCADE, null=True, blank=True,
                                        related_name='sent_messages_retailer')
    receiver_farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE, null=True, blank=True,
                                        related_name='received_messages_farmer')

    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        sender = self.sender_farmer or self.sender_retailer
        return f"Message from {sender} at {self.timestamp}"