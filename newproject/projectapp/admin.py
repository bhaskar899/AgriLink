from django.contrib import admin

from . models import Farmer,Retailer,Product,Order
# Register your models here.

admin.site.register(Farmer)
admin.site.register(Retailer)
admin.site.register(Product)
admin.site.register(Order)

