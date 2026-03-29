from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Team, DocumentSlot
from django.db.models.signals import post_delete

#@receiver(post_save, sender=Team)
#def notify_team_on_registration(sender, instance, created, **kwargs):
   # if created:
        #subject = 'Welcome to EVALX - Registration Successful'
        #message = f'Hello,\n\nYour team has been successfully registered.\nTeam ID: {instance.team_id}\n\nYou can now log in to the portal.'
        #recipient_list = [instance.user.email]
        
       # try:
            #send_mail(
                #subject,
                #message,
                #settings.DEFAULT_FROM_EMAIL,
                #recipient_list,
                #fail_silently=False,
           # )
           # print(f"✅ Success: Email sent to {instance.user.email}")
        #except Exception as e:
         #   print(f"❌ Email Error: {e}")

@receiver(post_save, sender=Team)
def notify_title_approval(sender, instance, created, **kwargs):
    if not created and instance.is_approved:
        subject = f"Project Title Approved: {instance.project_title}"
        message = (
            f"Hello Team {instance.team_id},\n\n"
            f"Your project title '{instance.project_title}' has been officially APPROVED.\n"
            f"You can now proceed with your documentation."
        )
        recipient_list = [m.user.email for m in instance.members.all()]
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
        print(f"✅ Approval Email sent to Team {instance.team_id}")

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime

@receiver(post_save, sender=DocumentSlot)
def notify_deadline_or_review(sender, instance, created, **kwargs):
    # This fires when a Coordinator updates a slot's deadline or review date
    subject = f"Schedule Updated: {instance.title}"
    
    # Helper to handle the 'str' vs 'date' object issue
    def get_date_str(date_val):
        if not date_val:
            return None
        # If it's already a string, try to format it or return as is
        if isinstance(date_val, str):
            try:
                return datetime.strptime(date_val, '%Y-%m-%d').strftime('%d %b, %Y')
            except:
                return date_val
        # If it's a date object, format it
        return date_val.strftime('%d %b, %Y')

    d_str = get_date_str(instance.deadline)
    r_str = get_date_str(instance.review_date)

    # Logic to customize message based on what was updated
    if r_str and d_str:
        body = f"Review Date: {r_str}\nSubmission Deadline: {d_str}"
    elif r_str:
        body = f"Review Date has been set for: {r_str}"
    else:
        body = f"Submission Deadline set for: {d_str}"

    message = f"Important Update for {instance.title}:\n\n{body}\n\nPlease check your dashboard for details."
    
    # Send to ALL active teams
    from .models import Team
    # Ensure we get a list of actual email strings
    recipient_list = list(Team.objects.values_list('user__email', flat=True))
    
    if recipient_list:
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
            print(f"✅ Bulk Notification sent for {instance.title}")
        except Exception as e:
            print(f"❌ Email failed: {e}")
            
@receiver(post_delete, sender=DocumentSlot)
def notify_on_deadline_deletion(sender, instance, **kwargs):
    """Fires an email to all teams when a coordinator removes a deadline or review date."""
    subject = f"Schedule Removed: {instance.title}"
    
    message = (
        f"Notice: The schedule for '{instance.title}' has been removed by the Coordinator.\n\n"
        f"Please check your dashboard for further updates or contact your guide for more information."
    )
    
    # Send to all registered teams
    recipient_list = list(Team.objects.values_list('user__email', flat=True))
    
    if recipient_list:
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
            print(f"⚠️ Deletion Notification sent for {instance.title}")
        except Exception as e:
            print(f"❌ Deletion Email Error: {e}")