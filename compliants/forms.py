from django import forms
from django.forms import ModelForm
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.forms import UserCreationForm
from .models import Contact, SatisfactionSurvey, User, Complaint, Category, Agency
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field

class MyUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['name', 'username', 'email', 'phone_number', 'address', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'form-control',
                'placeholder': f'Enter {field.label.lower()}'
            })

class UserForm(ModelForm):
    class Meta:
        model = User
        fields = ['name', 'username', 'email','phone_number', 'address', 'avatar']

class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['title', 'description', 'category', 'agency','document']

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter category name'
            })
        }

class AgencyForm(forms.ModelForm):
    class Meta:
        model = Agency
        fields = ['name', 'email', 'phone', 'address', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }            


class UserEditForm(UserChangeForm):
    password = None  # Remove password field from the form

    class Meta:
        model = User
        fields = ['email', 'name', 'phone_number', 'address', 'is_active', 'is_admin', 'is_agency_admin']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_admin': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_agency_admin': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ComplaintResponseForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['status', 'admin_response']
        widgets = {
            'admin_response': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Enter your detailed response here...'
            }),
            'status': forms.Select(attrs={'class': 'form-select'})
        }        



class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 5} ),
        }



class SatisfactionSurveyForm(forms.ModelForm):
    class Meta:
        model = SatisfactionSurvey
        fields = ['rating', 'comments', 'is_anonymous']
        widgets = {
            'rating': forms.RadioSelect(attrs={'class': 'rating-radio'}),
            'comments': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Optional feedback about your experience...'
            }),
        }