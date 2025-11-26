# newproject/asgi.py

import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import path


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'newproject.settings')
django_asgi_app = get_asgi_application()

# Consumers को अब यहाँ इम्पोर्ट करना सुरक्षित है
from projectapp.consumers import OrderChatConsumer, NotificationConsumer


application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": URLRouter(
        [
            path('ws/chat/<int:order_id>/', OrderChatConsumer.as_asgi()),
            path('ws/notifications/', NotificationConsumer.as_asgi()),
        ]
    ),
})