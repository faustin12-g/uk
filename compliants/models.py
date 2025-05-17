from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.core.validators import MinValueValidator, MaxValueValidator

class User(AbstractUser):
    name = models.CharField(max_length=200, null=True)
    email = models.EmailField(unique=True,null=True)
    phone_number = models.CharField(max_length=13, null=True)
    address = models.CharField(null=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_agency_admin = models.BooleanField(default=False)
    agency = models.ForeignKey("Agency", null=True, blank=True, on_delete=models.SET_NULL)
    avatar = models.ImageField(upload_to="images/",null=True, default="avatar.svg")

    @property
    def is_super_admin(self):
        return self.is_admin and not self.is_agency_admin

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username
    
class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Complaint(models.Model):
    CATEGORY_CHOICES = [
        ('health', 'Health'),
        ('infrastructure', 'Infrastructure'),
        ('security', 'Security'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('rejected', 'Rejected'),
    ]

    citizen = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints')
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    agency = models.ForeignKey('Agency', null=True, blank=True, on_delete=models.SET_NULL)
    document = models.FileField(
        upload_to='media/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    admin_response = models.TextField(null=True, blank=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    
    def save(self, *args, **kwargs):
       # Check if status is being changed to 'resolved'
       if self.status == 'resolved':
           if not self.resolved_at:
               self.resolved_at = timezone.now()
           
           # Check if this is a new resolution (not just updating an already resolved complaint)
           if not kwargs.get('update_fields') or 'status' in kwargs['update_fields']:
               from .utils import maybe_send_survey_email
               maybe_send_survey_email(self)
       
       super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.title} ({self.status})"

class Agency(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Contact(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('responded', 'Responded'),
    ]

    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_response = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    responded_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.subject} - {self.email}"

    def save(self, *args, **kwargs):
        if self.status == 'responded' and not self.responded_at:
            self.responded_at = timezone.now()
        super().save(*args, **kwargs)



class SatisfactionSurvey(models.Model):
    RATING_CHOICES = [
        (1, 'Very Dissatisfied'),
        (2, 'Dissatisfied'),
        (3, 'Neutral'),
        (4, 'Satisfied'),
        (5, 'Very Satisfied')
    ]

    complaint = models.OneToOneField(
        'Complaint',
        on_delete=models.CASCADE,
        related_name='survey'
    )
    rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comments = models.TextField(blank=True)
    completed_at = models.DateTimeField(auto_now_add=True)
    is_anonymous = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Satisfaction Surveys"
        ordering = ['-completed_at']

    def __str__(self):
        return f"Survey for Complaint #{self.complaint.id} ({self.get_rating_display()})"