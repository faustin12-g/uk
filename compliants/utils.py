from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from datetime import timedelta
from django.utils import timezone

def maybe_send_survey_email(complaint):
    """Send survey email if complaint was just resolved"""
    # Only send if complaint was resolved in the last minute
    # (to avoid duplicate sends if save() is called multiple times)
    if complaint.resolved_at and (timezone.now() - complaint.resolved_at) < timedelta(minutes=1):
        send_survey_email(complaint)

def send_survey_email(complaint):
    subject = f"We'd love your feedback on Complaint #{complaint.id}"
    survey_url = f"{settings.SITE_URL}/complaints/{complaint.id}/survey/"
    
    html_message = render_to_string('emails/survey_request.html', {
        'complaint': complaint,
        'survey_url': survey_url,
        'user': complaint.citizen
    })
    
    send_mail(
        subject,
        strip_tags(html_message),
        settings.DEFAULT_FROM_EMAIL,
        [complaint.citizen.email],
        html_message=html_message
    )