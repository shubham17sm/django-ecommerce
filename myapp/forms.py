from django import forms
from django.forms import ModelForm
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget
from .models import BilingAddress, UserProfile

PAYMENT_CHOICES = (
    ('S', 'Stripe'),
    ('P', 'PayPal')

)

ADDRESS_TYPE_CHOICES = (
    ('Home', 'Home'),
    ('Office', 'Office'),
    ('Other', 'Other')
)

class CheckoutForm(forms.Form):
    street_address = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder': '1234 Main St'
    }))
    apartment_address = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'placeholder': 'Apartment or suite'
    }))
    country = CountryField(blank_label='(select country)').formfield(widget=CountrySelectWidget(attrs={
        'class': 'custom-select d-block w-100',
        'id': 'country'
    }))
    zipcode = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control'
    }))
    same_shipping_address = forms.BooleanField(widget=forms.CheckboxInput(),  required=False)
    save_info = forms.BooleanField(widget=forms.CheckboxInput(), required=False)
    payment_option = forms.ChoiceField(widget=forms.RadioSelect, choices=PAYMENT_CHOICES)


class CreateAddressForm(forms.ModelForm):
    address_type = forms.ChoiceField(widget=forms.Select(attrs={
        'class': 'custom-select d-block w-100',
        'id': 'address'
    }), choices=ADDRESS_TYPE_CHOICES)
    street_address = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder': '1234 Main St'
    }))
    apartment_address = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'placeholder': 'Apartment or suite'
    }))
    country = CountryField(blank_label='(select country)').formfield(widget=CountrySelectWidget(attrs={
        'class': 'custom-select d-block w-100',
        'id': 'country'
    }))
    zipcode = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control'
    }))

    class Meta:
        model = BilingAddress
        fields = (
            'address_type', 'street_address','apartment_address', 'country', 'zipcode'
        )


class UserProfileForm(forms.ModelForm):
    firstname = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'placeholder': 'Enter Firstname',
        'id': 'firstName'
    }))
    lastname = forms.CharField(widget=forms.TextInput(attrs={
        'id': 'lastname', 
    }))
    email = forms.EmailField(widget=forms.TextInput(attrs={
        'id': 'email',
        'placeholder': 'youremail@example.com', 
    }))
    profile_picture = forms.ImageField()

    class Meta:
        model = UserProfile
        fields = (
            'firstname', 'lastname','email', 'profile_picture'
        )

        
    