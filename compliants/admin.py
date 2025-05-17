from django.contrib import admin

from compliants.views import send_contact_response
from .models import User, Category, Complaint, Agency, Contact, SatisfactionSurvey
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_str
from django.utils.html import strip_tags
from django.conf import settings





@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "phone_number", "address"]
    list_editable = ["email", "phone_number", "address"]
    list_per_page = 10
    ordering = ["name"] 
    search_fields = ["name__istartswith", "email", "phone_number__istartswith", "address__istartswith"]
    list_filter = ["is_admin"]

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name"]
    list_per_page = 10
    ordering = ["name"] 
    search_fields = ["name__istartswith"]


class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('title', 'citizen', 'category', 'status', 'created_at')
    list_filter = ('status', 'category')
    search_fields = ('title', 'description', 'citizen__name')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['mark_as_resolved']
    
    fieldsets = (
        (None, {
            'fields': ('citizen', 'title', 'description', 'category', 'status', 'document')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Admin Response', {
            'fields': ('admin_response',),
            'description': 'Your response will be emailed to the user'
        })
    )
    
    def mark_as_resolved(self, request, queryset):
        for complaint in queryset:
            complaint.status = 'resolved'
            complaint.save()
            self.send_resolution_email(complaint)
        self.message_user(request, f"{queryset.count()} complaints marked as resolved")
    
    def send_resolution_email(self, complaint):
        if complaint.admin_response:
            subject = f"Your Complaint #{complaint.id} Has Been Resolved"
            html_message = render_to_string('emails/complaint_resolved.html', {
                'complaint': complaint,
                'user': complaint.citizen
            })
            plain_message = strip_tags(html_message)
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [complaint.citizen.email],
                html_message=html_message
            )

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ["title", "citizen" , "category", "status", "agency", "created_at", "updated_at"]
    list_per_page = 10
    ordering = ["-created_at"] 
    search_fields = ["title__istartswith", "description__icontains", "category__name__istartswith", "agency__name__istartswith"]
    list_filter = ["status", "category", "agency"]
    readonly_fields = ["created_at", "updated_at"]
    actions = ["approve_complaints", "reject_complaints"]

    def approve_complaints(self, request, queryset):
        queryset.update(status="approved")
        def reject_complaints(self, request, queryset):
            queryset.update(status="rejected")
    def mark_as_resolved(self, request, queryset):
        queryset.update(status='resolved')
    mark_as_resolved.short_description = "Mark selected as resolved"         

@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "phone", "address", "is_active"]
    list_per_page = 10
    ordering = ["name"] 
    search_fields = ["name__istartswith", "email__istartswith", "phone__istartswith", "address__istartswith"]
    list_filter = ["is_active"]
     

class ContactAdmin(admin.ModelAdmin):
    list_display = ('subject', 'name', 'email', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('subject', 'name', 'email')
    readonly_fields = ('created_at', 'responded_at')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'email', 'subject', 'message', 'status')
        }),
        ('Response', {
            'fields': ('admin_response',),
            'description': 'Your response will be emailed to the user'
        }),
        ('Dates', {
            'fields': ('created_at', 'responded_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if obj.status == 'responded' and obj.admin_response:
            send_contact_response(obj)
        super().save_model(request, obj, form, change)

admin.site.register(Contact, ContactAdmin)


@admin.register(SatisfactionSurvey)
class SatisfactionSurveyAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'rating_stars', 'is_anonymous', 'completed_at')
    list_filter = ('rating', 'is_anonymous')
    search_fields = ('complaint__title', 'comments')
    readonly_fields = ('complaint', 'completed_at')
    
    def rating_stars(self, obj):
        return '★' * obj.rating + '☆' * (5 - obj.rating)
    rating_stars.short_description = 'Rating'