from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Employee, SiteUser, Authors


@receiver(post_save, sender=User)
def handle_user_profile(sender, instance, created, **kwargs):
    """
    При создании пользователя или изменении его типа (user_type)
    создаёт/обновляет соответствующий профиль.
    """
    if instance.user_type == "employee":
        profile, _ = Employee.objects.get_or_create(user=instance)
        profile.save()  # сохраняем на случай, если профиль уже был, но данные изменились
    elif instance.user_type == "author":
        profile, _ = Authors.objects.get_or_create(user=instance)
        profile.save()
    else:  # обычный пользователь
        profile, _ = SiteUser.objects.get_or_create(user=instance)
        profile.save()
