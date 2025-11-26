# projectapp/context_processors.py
from .models import Notification,Farmer,Retailer,Driver
def navbar_notifications(request):
    user_type = request.session.get('user_type')
    name = request.session.get('name')
    notes = []

    if user_type == "farmer" and name:
        notes = Notification.objects.filter(receiver_farmer__name=name, is_read=False).order_by('-timestamp')
    elif user_type == "retailer" and name:
        notes = Notification.objects.filter(receiver_retailer__name=name, is_read=False).order_by('-timestamp')
    elif user_type == "driver" and name:
        notes = Notification.objects.filter(receiver_driver__name=name, is_read=False).order_by('-timestamp')

    return {'navbar_notes': notes, 'user_type': user_type}