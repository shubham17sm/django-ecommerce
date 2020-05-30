from django import forms
from django.forms import ModelForm
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget
from .models import BilingAddress, UserProfile, DiscountCode, CheckZipcode

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
    default_address = forms.BooleanField(widget=forms.CheckboxInput(attrs={
        'type': 'checkbox',
        'class': 'custom-control-input',
        'name': 'same_billing_addess',
        'id': 'default-address'
    }), required=False)

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
    lastname = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'id': 'lastname', 
    }))
    email = forms.EmailField(required=False, widget=forms.TextInput(attrs={
        'id': 'email',
        'placeholder': 'youremail@example.com', 
    }))
    profile_picture = forms.ImageField()

    class Meta:
        model = UserProfile
        fields = (
            'firstname', 'lastname','email', 'profile_picture'
        )

class DiscountForm(forms.Form):
    promo_code = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Promo code',
        'aria-label': "Recipient's username",
        'aria-describedby': 'basic-addon2'
    }))

class CheckZipcodeForm(forms.Form):
    zipcode = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Check zipcode for delivery',
        'aria-label': 'zipcode checker',
        'aria-describedby': 'basic-addon2'
    }))

class RequestRefundForm(forms.Form):
    order_id = forms.CharField()
    message = forms.CharField(widget=forms.Textarea(attrs={
        'rows': 4
    }))
    email = forms.EmailField()