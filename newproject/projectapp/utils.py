# projectapp/utils.py

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


def send_realtime_notification(user_type, user_name, message):
    """
    एक विशिष्ट उपयोगकर्ता (ग्रुप) को रीयल-टाइम अधिसूचना भेजता है।
    """
    channel_layer = get_channel_layer()

    # यह ग्रुप नेम consumers.py में connect फ़ंक्शन के Group Name से मैच होना चाहिए
    group_name = f'notifications_{user_type}_{user_name}'

    # Consumer में 'send_notification' फ़ंक्शन को कॉल करने के लिए संदेश भेजें
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'send_notification',
            'message': message
        }
    )


import math

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Radius of Earth in KM

    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(d_lat / 2) ** 2 +
        math.cos(math.radians(lat1)) *
        math.cos(math.radians(lat2)) *
        math.sin(d_lon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c