from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import TokenEmailConfirmation
from .utils.generate_confirmation_token import generate_confirmation_token

from user.models import User, Tutor

@receiver(post_save, sender=User)
def email_token_confirmation_created(sender, instance, created, **kwargs):
    """
    Send an email with a token confirmation after the user is saved
    """
    if created:
        # Generate the confirmation token
        token = generate_confirmation_token(user=instance)
        
        # Construct the confirmation URL
        confirm_account_url = f"{settings.FRONTED_URL}/account/confirm-email/?token={token.token}"
        
        # Construct email content
        context = {
            'confirm_account_url': confirm_account_url,
        }
        email_html_message = render_to_string('core/user_confirm_email.html', context)
        email_plaintext_message = strip_tags(email_html_message)

        # Send the email
        msg = EmailMultiAlternatives(
            "Potwierdzenie adresu email",
            email_plaintext_message,
            settings.DEFAULT_FROM_EMAIL,
            [instance.email]
        )
        msg.attach_alternative(email_html_message, "text/html")
        msg.send()
        
        # Create and save the token
        token.save()
        
@receiver(pre_save, sender=Tutor)
def validate_tutor(sender, instance, **kwargs):
    """
    Can't create a tutor instance if the user is not a tutor
    """
    if instance.user.is_tutor != True:
        raise ValidationError("Invalid tutor instance. The user must be a tutor.")
    
@receiver(post_save, sender=User)
def create_tutor_if_user_is_tutor(sender, instance, created, **kwargs):
    """
    Create a tutor instance if the user is a tutor
    """
    if created and instance.is_tutor:
        Tutor.objects.create(user=instance) 
        
    if Tutor.objects.filter(user=instance).exists() and not instance.is_tutor:
        Tutor.objects.get(user=instance).delete()