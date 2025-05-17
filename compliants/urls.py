from django.urls import path
from django.contrib.auth import views as auth_views
from .views import *


urlpatterns = [
    path('', home_page, name='home'),
    path('signup/', register_page, name='signup'),
    path('activate/<uidb64>/<token>/', activate_account, name='activate'),
    path('login/', login_page, name='login'),
    path('logout', logout_page, name="logout"),
    path('update-user/', update_profile, name="update-user"),
    path('about/', about_page, name="about"),
    path('faq/', faq_page, name="faq"),

 # Password reset
    path('reset_password/', auth_views.PasswordResetView.as_view(template_name="reset/password_reset.html"), name="reset_password"),
    path('reset_password_sent/', auth_views.PasswordResetDoneView.as_view(template_name="reset/password_reset.html"), name="password_reset_done"),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name="reset/password_reset_form.html"), name="password_reset_confirm"),
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(template_name="reset/password_reset_done.html"), name="password_reset_complete"),


    path('complaints/submit/', submit_complaint, name='submit_complaint'),
    path('complaints/', complaint_list, name='complaint_list'),
    path('complaints/update/<int:pk>/', update_complaint, name='update_complaint'),
    path('complaints/delete/<int:pk>/', delete_complaint, name='delete_complaint'),
    path('complaints/<int:pk>/', complaint_detail, name='complaint_detail'),

    path('dashboard/', dashboard, name='admin_dashboard'),
    path('export-complaints/', export_complaints, name='export_complaints'),
    path('categories/', admin_categories, name='admin_categories'),
    path('categories/add/', admin_category_add, name='admin_category_add'),
    path('categories/<int:pk>/edit/', admin_category_edit, name='admin_category_edit'),
    path('categories/<int:pk>/delete/', admin_category_delete, name='admin_category_delete'),

    path('agencies/', admin_agencies, name='admin_agencies'),
    path('agencies/add/', admin_agency_add, name='admin_agency_add'),
    path('agencies/<int:pk>/edit/', admin_agency_edit, name='admin_agency_edit'),
    path('agencies/<int:pk>/delete/', admin_agency_delete, name='admin_agency_delete'),

    path('users/', admin_users, name='admin_users'),
    path('users/<int:pk>/edit/', admin_user_edit, name='admin_user_edit'),
    path('users/<int:pk>/delete/', admin_user_delete, name='admin_user_delete'),
    path('users/<int:pk>/toggle-status/', admin_user_toggle_status, name='admin_user_toggle_status'),

    path('reports/', admin_reports, name='admin_reports'),
    path('reports/complaints/', complaint_reports, name='complaint_reports'),
    path('reports/agencies/', agency_reports, name='agency_reports'),
    path('reports/users/', user_reports, name='user_reports'),
    path('reports/export/', export_reports, name='export_reports'),

    path('contact/', contact_support, name='contact_support'),
    path('contacts/', AdminContactMessageList.as_view(), name='admin_contact_messages'),
    path('acontacts/unresponded/', AdminUnrespondedContactList.as_view(), name='admin_unresponded_contacts'),
    path('contacts/<int:pk>/', AdminContactMessageDetail.as_view(), name='admin_contact_detail'),

    path('complaints/<int:pk>/survey/', complaint_survey, name='complaint_survey'),


]