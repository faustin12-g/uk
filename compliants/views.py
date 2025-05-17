import json
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import get_object_or_404, render, redirect
from django.db.models import Q, Count, Max
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.utils.html import strip_tags
from django.shortcuts import render, redirect
from django.http import JsonResponse
from datetime import datetime, timedelta
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
import csv
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import UserPassesTestMixin
from .models import *
from .forms import *



def login_page(request):
    page = 'login'
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email)
            if user.is_active == False:
              
              messages.info(request, "Your accout has been deactivated by administrator. Request to activate")

        except:
            messages.error(request, 'User does not exist')  

        user = authenticate(request, email=email, password=password)

       
        if user is not None:
            login(request, user)
            return redirect('complaint_list')
        else:
            messages.error(request, 'Username or password is not correct') 

    context = {'page': page}
    return render(request, 'login_register.html', context)


def logout_page(request):
    logout(request)
    return redirect('home')

def register_page(request):
    form = MyUserCreationForm()

    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.is_active = False  # Don't activate until email confirmation
            user.save()

            # Send activation email
            current_site = get_current_site(request)
            subject = "Activate Your Account"
            message = render_to_string('activate_account.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])
            messages.info(request, "Check your email to activate your account. If you don't receive an email, please check your spam folder.")
            return redirect('login')
    return render(request, 'login_register.html', {'form': form})


def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except:
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Account activated successfully.")
        return redirect('login')
    else:
        messages.error(request, "Activation link is invalid.")
        return redirect('home')


def home_page(request):
    return render(request, "home.html")

def faq_page(request):
    return render(request, "faq.html")


@login_required(login_url='login')
def update_profile(request):
    user = request.user
    form = UserForm(instance= user)
     
    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('home')

    context = {'form': form}
    return render(request, 'update-user.html', context)

def about_page(request):
    return render(request, "about.html")
def submit_complaint(request):
    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.citizen = request.user
            complaint.save()
            
            # Send confirmation email
            send_complaint_confirmation(complaint)
            
            messages.success(request, 'Your complaint has been submitted successfully!')
            return redirect('complaint_list')
    else:
        form = ComplaintForm()
    
    return render(request, 'complaints/submit_complaint.html', {'form': form})

def send_complaint_confirmation(complaint):
    subject = f"Complaint Received: {complaint.title}"
    html_message = render_to_string('emails/complaint_received.html', {
        'complaint': complaint,
        'user': complaint.citizen
    })
    plain_message = strip_tags(html_message)
    from_email = settings.DEFAULT_FROM_EMAIL
    to = complaint.citizen.email
    
    send_mail(subject, plain_message, from_email, [to], html_message=html_message)


def complaint_detail(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk)
    
    if request.method == 'POST':
        form = ComplaintResponseForm(request.POST, instance=complaint)
        if form.is_valid():
            complaint = form.save()
            
            if complaint.status == 'resolved' and complaint.admin_response:
                send_resolution_email(complaint)
                
            messages.success(request, 'Response submitted successfully!')
            return redirect('admin_dashboard')
    else:
        form = ComplaintResponseForm(instance=complaint)
    
    context = {
        'complaint': complaint,
        'form': form
    }
    return render(request, 'complaints/detail.html', context)

def send_resolution_email(complaint):
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



@login_required
def complaint_list(request):
    query = request.GET.get("q")
    complaints = Complaint.objects.filter(citizen=request.user)

    if query:
        complaints = complaints.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(agency__name__icontains=query)
        )

    # Check if it's an AJAX request
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('complaints/_complaint_table.html', {'complaints': complaints})
        return JsonResponse({'html': html})
    hour = datetime.now().hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 18:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"
    context = {'complaints': complaints, 'greeting': greeting}

    return render(request, 'complaints/complaint_list.html', context)


@login_required
def update_complaint(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk, citizen=request.user)
    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES, instance=complaint)
        if form.is_valid():
            form.save()
            messages.success(request, "Complaint updated successfully.")
            return redirect('complaint_list')
    else:
        form = ComplaintForm(instance=complaint)
    return render(request, 'complaints/update_complaint.html', {'form': form})


@login_required
def delete_complaint(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk, citizen=request.user)
    if request.method == 'POST':
        complaint.delete()
        messages.success(request, "Complaint deleted successfully.")
        return redirect('complaint_list')
    return redirect('complaint_list')


def admin_check(user):
    return user.is_authenticated and (user.is_admin or user.is_agency_admin)
from .models import Contact  # Import your model

def admin_check(user):
    return user.is_authenticated and (user.is_admin or user.is_agency_admin)

@user_passes_test(admin_check)
def dashboard(request):
    # Complaints Stats
    total_complaints = Complaint.objects.count()
    resolved_complaints = Complaint.objects.filter(status='resolved').count()
    pending_complaints = Complaint.objects.filter(status='pending').count()

    if request.user.is_agency_admin:
        complaints = Complaint.objects.filter(agency=request.user.agency)
        notifications = complaints.filter(status__in=['pending', 'in_progress'])
    else:
        complaints = Complaint.objects.all()
        notifications = Complaint.objects.filter(status__in=['pending', 'in_progress'])

    categories = Category.objects.annotate(
        total=Count('complaint'),
        resolved=Count('complaint', filter=Q(complaint__status='resolved'))
    )

    status_data = complaints.values('status').annotate(count=Count('status'))

    # Contact Stats
    total_contacts = Contact.objects.count()
    pending_contacts = Contact.objects.filter(status='pending').count()
    responded_contacts = Contact.objects.filter(status='responded').count()
    recent_contacts = Contact.objects.order_by('-created_at')[:5]

    context = {
        'total_complaints': total_complaints,
        'resolved_complaints': resolved_complaints,
        'pending_complaints': pending_complaints,
        'categories': categories,
        'status_data': status_data,
        'recent_complaints': complaints.order_by('-created_at')[:10],
        'notifications_count': notifications.count(),
        
        # Contact Data
        'total_contacts': total_contacts,
        'pending_contacts': pending_contacts,
        'responded_contacts': responded_contacts,
        'recent_contacts': recent_contacts,
    }
    return render(request, 'admin/dashboard.html', context)

    

def export_complaints(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="complaints.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['ID', 'Title', 'Category', 'Status', 'Created At'])
    
    complaints = Complaint.objects.all()
    for complaint in complaints:
        writer.writerow([
            complaint.id,
            complaint.citizen.name,
            complaint.title,
            complaint.description,
            complaint.document,
            complaint.category.name,
            complaint.get_status_display(),
            complaint.created_at.strftime("%Y-%m-%d")
        ])
    
    return response

@user_passes_test(admin_check)
@login_required
def admin_categories(request):
    categories = Category.objects.all()
    context = {
        'categories': categories,
        'active_tab': 'admin_categories',
        'pending_complaints_count': Complaint.objects.filter(status='pending').count()
    }
    return render(request, 'admin/categories.html', context)


@user_passes_test(admin_check)
@login_required
def admin_category_add(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category added successfully!')
            return redirect('admin_categories')
    else:
        form = CategoryForm()
    
    context = {'form': form}
    return render(request, 'admin/category_add.html', context)

@user_passes_test(admin_check)
@login_required
def admin_category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully!')
            return redirect('admin_categories')
    else:
        form = CategoryForm(instance=category)
    
    context = {'form': form, 'category': category}
    return render(request, 'admin/category_edit.html', context)

@user_passes_test(admin_check)
@login_required
def admin_category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted successfully!')
        return redirect('admin_categories')
    
    context = {'category': category}
    return render(request, 'admin/category_confirm_delete.html', context)


# AGENCY ADMIN VIEWS

@user_passes_test(admin_check)
@login_required
def admin_agencies(request):
    agencies = Agency.objects.all()
    context = {
        'agencies': agencies,
        'pending_complaints_count': Complaint.objects.filter(status='pending').count()
    }
    return render(request, 'admin/agencies.html', context)

@user_passes_test(admin_check)
@login_required
def admin_agency_add(request):
    if request.method == 'POST':
        form = AgencyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Agency added successfully!')
            return redirect('admin_agencies')
    else:
        form = AgencyForm()
    
    context = {'form': form}
    return render(request, 'admin/agency_add.html', context)

@user_passes_test(admin_check)
@login_required
def admin_agency_edit(request, pk):
    agency = get_object_or_404(Agency, pk=pk)
    if request.method == 'POST':
        form = AgencyForm(request.POST, instance=agency)
        if form.is_valid():
            form.save()
            messages.success(request, 'Agency updated successfully!')
            return redirect('admin_agencies')
    else:
        form = AgencyForm(instance=agency)
    
    context = {'form': form, 'agency': agency}
    return render(request, 'admin/agency_edit.html', context)

@user_passes_test(admin_check)
@login_required
def admin_agency_delete(request, pk):
    agency = get_object_or_404(Agency, pk=pk)
    if request.method == 'POST':
        agency.delete()
        messages.success(request, 'Agency deleted successfully!')
        return redirect('admin_agencies')
    
    context = {'agency': agency}
    return render(request, 'admin/agency_confirm_delete.html', context)


# USER MANAGEMENT VIEWS
@user_passes_test(admin_check)
@login_required
def admin_users(request):
    users = User.objects.all().order_by('-date_joined')
    context = {
        'users': users,
        'pending_complaints_count': Complaint.objects.filter(status='pending').count()
    }
    return render(request, 'admin/users.html', context)

@user_passes_test(admin_check)
@login_required
def admin_user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'User {user.email} updated successfully!')
            return redirect('admin_users')
    else:
        form = UserEditForm(instance=user)
    
    context = {'form': form, 'user': user}
    return render(request, 'admin/user_edit.html', context)

@user_passes_test(admin_check)
@login_required
def admin_user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.delete()
        messages.success(request, f'User {user.email} deleted successfully!')
        return redirect('admin_users')
    
    context = {'user': user}
    return render(request, 'admin/user_confirm_delete.html', context)

@user_passes_test(admin_check)
@login_required
def admin_user_toggle_status(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.is_active = not user.is_active
    user.save()
    status = "activated" if user.is_active else "deactivated"
    messages.success(request, f'User {user.email} has been {status}.')
    return redirect('admin_users')


# REPORT VIEWS

@user_passes_test(admin_check)
@login_required
def admin_reports(request):
    # Basic stats for the reports dashboard
    context = {
        'pending_complaints_count': Complaint.objects.filter(status='pending').count(),
        'resolved_complaints_count': Complaint.objects.filter(status='resolved').count(),
        'total_agencies': Agency.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
    }
    return render(request, 'admin/reports/dashboard.html', context)

@user_passes_test(admin_check)
@login_required
def complaint_reports(request):
    # Complaint statistics
    complaints = Complaint.objects.all()
    
    # Last 30 days data
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_complaints = complaints.filter(created_at__gte=thirty_days_ago)
    
    # Status distribution
    status_data = complaints.values('status').annotate(count=Count('status'))
    
    # Category distribution
    category_data = complaints.values('category__name').annotate(
        count=Count('category'),
        resolved=Count('category', filter=Q(status='resolved'))
    )
    
    context = {
        'total_complaints': complaints.count(),
        'status_data': status_data,
        'category_data': category_data,
        'recent_complaints': recent_complaints,
    }
    return render(request, 'admin/reports/complaints.html', context)

@user_passes_test(admin_check)
@login_required
def agency_reports(request):
    agencies = Agency.objects.annotate(
        total_complaints=Count('complaint'),
        resolved_complaints=Count('complaint', filter=Q(complaint__status='resolved')),
        pending_complaints=Count('complaint', filter=Q(complaint__status='pending')),
    )
    
# Prepare data for chart
    agency_names = [agency.name for agency in agencies]
    total = [agency.total_complaints for agency in agencies]
    resolved = [agency.resolved_complaints for agency in agencies]
    pending = [agency.pending_complaints for agency in agencies]
    user_names = [ user.username for user in User.objects.filter(is_active=True) ]
    user_complaints = [ user.complaints_submitted for user in User.objects.filter(is_active=True) ]
    
    context = {
        'agencies': agencies,
        'agency_names': json.dumps(agency_names),  # ✅ Use correct variable
        'agency_total': json.dumps(total),
        'agency_resolved': json.dumps(resolved),
        'agency_pending': json.dumps(pending),
        'user_names': json.dumps(user_names),           # Make sure these are defined too
        'user_complaints': json.dumps(user_complaints), # Make sure these are defined too
    }
    return render(request, 'admin/reports/agencies.html', context)

@user_passes_test(admin_check)
@login_required
def user_reports(request):
    users = User.objects.annotate(
        complaints_submitted=Count('complaints'),
        last_active=Max('last_login'),
    ).order_by('-complaints_submitted')

    user_names = [user.username for user in users]
    complaint_counts = [user.complaint_count for user in users]
    
    context = {
        'active_users': users.filter(is_active=True),
        'inactive_users': users.filter(is_active=False),
        'user_names': json.dumps(user_names, cls=DjangoJSONEncoder),
        'user_complaints': json.dumps(complaint_counts, cls=DjangoJSONEncoder),
    }
    return render(request, 'admin/reports/users.html', context)

@user_passes_test(admin_check)
@login_required
def export_reports(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="reports_export_{}.csv"'.format(
        datetime.now().strftime("%Y%m%d")
    )
    
    writer = csv.writer(response)
    
    # Write headers
    writer.writerow(['Report Type', 'Metric', 'Value', 'Date Generated'])
    
    # Add complaint data
    complaints = Complaint.objects.all()
    writer.writerow(['Complaints', 'Total', complaints.count(), datetime.now()])
    writer.writerow(['Complaints', 'Resolved', complaints.filter(status='resolved').count(), datetime.now()])
    writer.writerow(['Complaints', 'Pending', complaints.filter(status='pending').count(), datetime.now()])
    
    # Add agency data
    agencies = Agency.objects.count()
    writer.writerow(['Agencies', 'Total', agencies, datetime.now()])
    
    # Add user data
    users = User.objects.filter(is_active=True).count()
    writer.writerow(['Users', 'Active', users, datetime.now()])
    
    return response


# contact support views

def contact_support(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save()
            send_contact_confirmation(contact)
            messages.success(request, 'Your message has been sent! We will contact you soon.')
            return redirect('home')
    else:
        form = ContactForm()
    
    return render(request, 'contact/contact_form.html', {'form': form})

def send_contact_confirmation(contact):
    subject = f"Contact Received: {contact.subject}"
    html_message = render_to_string('emails/contact_received.html', {
        'contact': contact
    })
    plain_message = strip_tags(html_message)
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [contact.email],
        html_message=html_message
    )

def send_contact_response(contact):
    subject = f"Re: {contact.subject}"
    html_message = render_to_string('emails/contact_response.html', {
        'contact': contact
    })
    plain_message = strip_tags(html_message)
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [contact.email],
        html_message=html_message
    )


# contact admin views

class AdminContactMessageList(UserPassesTestMixin, ListView):
    model = Contact
    template_name = 'admin/contact_list.html'
    context_object_name = 'contacts'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.is_admin
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unresponded_messages_count'] = Contact.objects.filter(status='pending').count()
        return context

class AdminUnrespondedContactList(AdminContactMessageList):
    def get_queryset(self):
        return Contact.objects.filter(status='pending').order_by('-created_at')

class AdminContactMessageDetail(UserPassesTestMixin, DetailView):
    model = Contact
    template_name = 'admin/contact_detail.html'
    context_object_name = 'contact'
    
    def test_func(self):
        return self.request.user.is_admin
    
    def post(self, request, *args, **kwargs):
        contact = self.get_object()
        response_text = request.POST.get('response', '')
        
        if response_text:
            contact.admin_response = response_text
            contact.status = 'responded'
            contact.save()
            
            # Send response email
            send_contact_response(contact)
            
            messages.success(request, 'Response sent successfully!')
            return redirect('admin_contact_detail', pk=contact.pk)
        
        return self.get(request, *args, **kwargs)



# user satisfaction survey views


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

def complaint_survey(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk, status='resolved')
    
    # Check if survey already exists
    if hasattr(complaint, 'survey'):
        messages.info(request, 'You have already completed this survey.')
        return redirect('complaint_detail', pk=pk)
    
    if request.method == 'POST':
        form = SatisfactionSurveyForm(request.POST)
        if form.is_valid():
            survey = form.save(commit=False)
            survey.complaint = complaint
            survey.save()
            
            messages.success(request, 'Thank you for your feedback!')
            return redirect('complaint_detail', pk=pk)
    else:
        form = SatisfactionSurveyForm()
    
    context = {
        'complaint': complaint,
        'form': form
    }
    return render(request, 'complaints/survey.html', context)
