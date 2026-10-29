from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import AuditEvent
@receiver(post_save, sender=get_user_model())
def audit_user_save(sender, instance, created, **kwargs):
    # Avoid logging passwords or other credentials.
    AuditEvent.objects.create(actor=instance if not created else None, action="created" if created else "updated",
                              model_label="accounts.User", object_id=str(instance.pk),
                              summary=f"User account {'created' if created else 'updated'}")
