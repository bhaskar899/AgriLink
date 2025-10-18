from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from . import views
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),

    #  Root URL ab directly home par redirect karega
    path("", lambda request: redirect("home"), name="root"),

    #  Main pages
    path("home/", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),

    #  Farmer URLs
    path("farmer_register/", views.farmer_register, name="farmer_register"),
    path("farmer_login/", views.farmer_login, name="farmer_login"),
    path("farmer_dashboard/", views.farmer_dashboard, name="farmer_dashboard"),
    path("add_product/", views.add_product, name="add_product"),
    path("show_products/", views.show_products, name="show_products"),
    path("farmer_order/",views.farmer_order,name="farmer_order"),

    path("update_status/<int:order_id>/",views.update_status,name="update_status"),

    # 🛍 Retailer URLs
    path("browse_products/", views.browse_products, name="browse_products"),
    path("retailer_dashboard/", views.retailer_dashboard, name="retailer_dashboard"),
    path("retailer_login/", views.retailer_login, name="retailer_login"),
    path("retailer_register/", views.retailer_register, name="retailer_register"),
    path("retailer_products/", views.retailer_products, name="retailer_products"),
    path("track_order/<int:order_id>/", views.track_order, name="track_order"),
    path("place_order/<int:product_id>/", views.place_order, name="place_order"),

    #  Logout
    path("logout/", views.logout, name="logout"),

    path('chat/<int:order_id>/', views.chat_view, name='chat'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)