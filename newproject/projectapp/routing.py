# projectapp/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<order_id>\d+)/$', consumers.OrderChatConsumer.as_asgi()),
    re_path(r'ws/notify/$', consumers.NotificationConsumer.as_asgi()),
]

# Note: यहाँ कोई 'import os', 'get_asgi_application()', या 'application =' नहीं होना चाहिए।