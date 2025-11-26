# projectapp/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.db.models import Q
from .models import ChatMessage, Order, Farmer, Retailer  # Farmer/Retailer इम्पोर्ट किए गए
from django.shortcuts import get_object_or_404  # ऑब्जेक्ट्स को फेच करने के लिए
# projectapp/consumers.py

# आवश्यक Django Imports
import json
from channels.generic.websocket import AsyncWebsocketConsumer

# 🛑 CRITICAL FIX: Add Django setup here
# यह सुनिश्चित करता है कि यदि यह फ़ाइल सीधे (asgi.py के माध्यम से) इम्पोर्ट होती है,
# तो Django apps लोड हो जाते हैं।
import django
django.setup()

# अब Models को Import करें (यह अब सुरक्षित है)
from .models import ChatMessage, Order, Farmer, Retailer
# Farmer/Retailer इम्पोर्ट किए गए

# ... बाकी Consumers का कोड यहाँ आता है ...

# --- Helper Function (Message Serialization) ---
def _message_to_dict_for_ws(msg):
    """Converts a ChatMessage model instance to a dict for WebSocket transport."""

    # ⚠️ FIX: Sender name को सुरक्षित रूप से एक्सेस करें
    if msg.sender_farmer:
        sender_name = msg.sender_farmer.name
        sender_type = 'farmer'
    elif msg.sender_retailer:
        sender_name = msg.sender_retailer.name
        sender_type = 'retailer'
    else:
        sender_name = "System"
        sender_type = "system"

    return {
        'id': msg.id,
        'sender_type': sender_type,  # added for easier JS handling
        'sender_name': sender_name,
        'message': msg.message,
        'image': msg.image.url if msg.image else None,
        'document': msg.document.url if msg.document else None,
        'voice': msg.voice.url if msg.voice else None,
        'timestamp': msg.timestamp.strftime('%b %d, %I:%M %p'),
        'is_seen': msg.is_seen,
    }


class NotificationConsumer(AsyncWebsocketConsumer):
    # ... (No changes needed here based on the chat issue)
    async def connect(self):
        user_name = self.scope['session'].get('name', 'guest')
        user_type = self.scope['session'].get('user_type', 'guest')
        self.group_name = f'notifications_{user_type}_{user_name}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_notification(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({'message': message}))


class OrderChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.order_id = self.scope['url_route']['kwargs']['order_id']
        self.group_name = f"order_{self.order_id}"

        # User details को session से fetch करें
        self.user_type = self.scope['session'].get('user_type')
        self.user_id = self.scope['session'].get('id')  # Assuming 'id' holds the profile ID

        if not self.user_id or not self.user_type:
            # यदि लॉग-इन नहीं है तो कनेक्शन अस्वीकार करें
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # --- Database Access Functions ---
    @database_sync_to_async
    def create_message(self, data):
        """Creates a new ChatMessage object in the database."""

        # ⚠️ FIX: Senders को सेशन ID से fetch करें
        order = get_object_or_404(Order, id=self.order_id)
        sender_farmer = None
        sender_retailer = None

        if self.user_type == 'farmer':
            # session ID का उपयोग करके Farmer को fetch करें
            sender_farmer = get_object_or_404(Farmer, id=self.user_id)
        elif self.user_type == 'retailer':
            # session ID का उपयोग करके Retailer को fetch करें
            sender_retailer = get_object_or_404(Retailer, id=self.user_id)
        else:
            return None  # Invalid user type

        new_msg = ChatMessage.objects.create(
            order=order,
            sender_farmer=sender_farmer,
            sender_retailer=sender_retailer,
            message=data.get("message"),
            message_type=data.get("message_type", "text"),
            # Files यहाँ नहीं आ सकते, वे HTTP View से आते हैं
        )
        return _message_to_dict_for_ws(new_msg)

    @database_sync_to_async
    def mark_seen(self):
        """Marks unseen messages sent by the other party as seen."""
        order = get_object_or_404(Order, id=self.order_id)

        # ⚠️ FIX: Mark Seen Logic को लागू किया गया
        if self.user_type == 'farmer':
            # Farmer देख रहा है, इसलिए retailer के भेजे गए messages को seen मार्क करें
            ChatMessage.objects.filter(
                order=order,
                sender_retailer=order.retailer,  # Retailer ने भेजा
                sender_farmer=None,  # और Farmer को प्राप्त हुआ
                is_seen=False
            ).update(is_seen=True)
        elif self.user_type == 'retailer':
            # Retailer देख रहा है, इसलिए farmer के भेजे गए messages को seen मार्क करें
            ChatMessage.objects.filter(
                order=order,
                sender_farmer=order.farmer,  # Farmer ने भेजा
                sender_retailer=None,  # और Retailer को प्राप्त हुआ
                is_seen=False
            ).update(is_seen=True)
        # Note: ChatMessage model में receiver fields होना बेहतर है,
        # लेकिन आपके current logic के अनुसार इसे Farmer/Retailer sender field से deduce किया गया है।
        return True

    @database_sync_to_async
    def delete_messa(self, msg_id):
        # ⚠️ FIX: Permissions check के लिए self.user_type का उपयोग करें
        try:
            msg = ChatMessage.objects.get(id=msg_id, order_id=self.order_id)

            # सिर्फ़ संदेश भेजने वाला ही इसे डिलीट कर सकता है (उदाहरण)
            if (self.user_type == 'farmer' and msg.sender_farmer and msg.sender_farmer.id == self.user_id) or \
                    (self.user_type == 'retailer' and msg.sender_retailer and msg.sender_retailer.id == self.user_id):
                # यदि इमेज या फ़ाइल है, तो उसे भी डिलीट करने का लॉजिक यहाँ जोड़ें (जैसे मैंने पिछले उत्तर में बताया था)
                msg.delete()
                return True
            return False  # Permission denied
        except ChatMessage.DoesNotExist:
            return False

    # --- Event Handlers (No changes needed) ---
    async def new_message(self, event):
        await self.send(text_data=json.dumps({"event": "new_message", "message": event['message']}))

    async def typing_event(self, event):
        await self.send(text_data=json.dumps({"event": "typing", "sender": event['sender'], "typing": event['typing']}))

    async def seen_event(self, event):
        await self.send(text_data=json.dumps({"event": "seen"}))

    async def delete_event(self, event):
        await self.send(text_data=json.dumps({"event": "delete", "message_id": event['message_id']}))

    # --- Receive Handler (No functional changes, logic shifted to DB calls) ---
    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        action = data.get("action")

        if action == "typing":
            await self.channel_layer.group_send(self.group_name, {
                "type": "typing_event",
                "sender": data.get("sender_type"),
                "typing": data.get("typing", False),
            })
        elif action == "seen":
            await self.mark_seen()
            # आपको यहाँ channel_layer.group_send नहीं करना चाहिए,
            # क्योंकि mark_seen_view पहले से ही group_send कर रहा है।
            # यदि आप WS से ही seen इवेंट भेजते हैं, तो डुप्लीकेट हो सकता है।
            # client side पर mark_seen_view को कॉल करना ही बेहतर है।
            # अगर सिर्फ़ WS से करना है, तो यह करें:
            # await self.channel_layer.group_send(self.group_name, {"type": "seen_event"})
            pass  # फिलहाल पास करें

        elif action == "send_message":
            msg_dict = await self.create_message(data)
            if msg_dict:
                await self.channel_layer.group_send(self.group_name, {
                    "type": "new_message",
                    "message": msg_dict,
                })
        elif action == "delete":
            msg_id = data.get("message_id")
            deleted = await self.delete_messa(msg_id)
            if deleted:
                await self.channel_layer.group_send(self.group_name, {
                    "type": "delete_event",
                    "message_id": msg_id,
                })