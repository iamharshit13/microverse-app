from django.db.models.signals import post_save
from django.dispatch import receiver
from .kafka_producer import send_event
from django.contrib.auth.models import User

@receiver(post_save, sender=User)
def send_user_creation_event(sender, instance, created, **kwargs):
    if created:
        event_data = {
            'user_id': instance.id,
            'username': instance.username,
            'email': instance.email,
            'action': 'user_created'
        }
        send_event('user-events', event_data)
