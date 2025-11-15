from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Employee, SiteUser, Authors

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.user_type == 'employee':
            Employee.objects.create(user=instance)
        elif instance.user_type == 'author':
            Authors.objects.create(user=instance)
        else:
            SiteUser.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if instance.user_type == 'employee' and hasattr(instance, 'employee_profile'):
        instance.employee_profile.save()
    elif instance.user_type == 'author' and hasattr(instance, 'author_profile'):
        instance.author_profile.save()
    elif instance.user_type == 'user' and hasattr(instance, 'site_user_profile'):
        instance.site_user_profile.save()