from django.contrib import admin

from .models import Farmer, Retailer, Product, Order, SampleRequest
# Register your models here.

from django.contrib import admin
from .models import Farmer, Retailer, Product, Order, Driver, Delivery
from .models import ChatMessage


admin.site.register(ChatMessage)

admin.site.register(Farmer)
admin.site.register(Retailer)
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(Driver)
admin.site.register(Delivery)
admin.site.register(SampleRequest)
