from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Root redirect
    path("", lambda request: redirect("home"), name="root"),

    # Main pages
    path("home/", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("contact_submit/",views.contact_submit,name="contact_submit"),

    # Farmer
    path("farmer_register/", views.farmer_register, name="farmer_register"),
    path("farmer_login/", views.farmer_login, name="farmer_login"),
    path("farmer_dashboard/", views.farmer_dashboard, name="farmer_dashboard"),
    path("add_product/", views.add_product, name="add_product"),
    path("show_products/", views.show_products, name="show_products"),
    path("farmer_order/", views.farmer_order, name="farmer_order"),
    path("update_status/<int:order_id>/", views.update_status, name="update_status"),

    # Retailer
    path("browse_products/", views.browse_products, name="browse_products"),
    path("retailer_dashboard/", views.retailer_dashboard, name="retailer_dashboard"),
    path("retailer_login/", views.retailer_login, name="retailer_login"),
    path("retailer_register/", views.retailer_register, name="retailer_register"),
    path("retailer_products/", views.retailer_products, name="retailer_products"),
    path("track_order/<int:order_id>/", views.track_order, name="track_order"),
    path("place_order/<int:product_id>/", views.place_order, name="place_order"),

    # chat + notifications
    path('chat/<int:order_id>/', views.chat_view, name='chat'),
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/read/<int:nid>/', views.mark_notification_read, name='mark_notification_read'),

    # Logout
    path("logout/", views.logout, name="logout"),

    # Real time Payments
# urls.py (update)
path('payment/<int:order_id>/', views.payment_page, name='payment_page'),
path('payment_success/<int:order_id>/', views.payment_success, name='payment_success'),
    path("place_order/<int:product_id>/",views.place_order,name="place_order"),

    path("generate_receipt/<int:order_id>/",views.generate_receipt,name="generate_receipt"),

    # search & fiter

    path("ajax_search/",views.ajax_search,name="ajax_search"),

    # training mode

    path('training/', views.training, name='training'),
path("training_complete/", views.training_complete, name="training_complete"),

path("profile/", views.profile, name="profile"),
path("profile_update/", views.profile_update, name="profile_update"),
path("profile_delete/", views.profile_delete, name="profile_delete"),
path("profile_delete_confirm/", views.profile_delete_confirm, name="profile_delete_confirm"),

    #forget password

path("forgot_password/", views.forgot_password, name="forgot_password"),
path("verify_otp/", views.verify_otp, name="verify_otp"),
path("reset_password/", views.reset_password, name="reset_password"),

]

# ✅ Serve media files in development only
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)