from django.db import models
from django.conf import settings
from django.shortcuts import reverse
from django_countries.fields import CountryField
from django.db.models.signals import post_save
from django.dispatch import receiver

# CATEGORY_CHOICES = (
#     ('S', 'Shirt'),
#     ('SW', 'Sport wear'),
#     ('OW', 'Outwear')
# )

LABEL_CHOICES = (
    ('P', 'primary'),
    ('S', 'secondary'),
    ('D', 'danger')
)

LABEL_NAME_CHOICES = (
    ('N', 'NEW'),
    ('S', 'SALE'),
    ('D', 'DISCOUNT'),
    ('O', 'OFFER')
)

ADDRESS_TYPE_CHOICES = (
    ('Home', 'Home'),
    ('Office', 'Office'),
    ('Other', 'Other')
)


class Category(models.Model):
    title = models.CharField(max_length=40)
    slug = models.SlugField()

    def __str__(self):
        return self.title



class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    firstname = models.CharField(max_length=120, null=True, blank=True)
    lastname = models.CharField(max_length=120, null=True, blank=True)
    email = models.EmailField(max_length=120, null=True, blank=True)
    profile_picture = models.ImageField(default='default_user.png')

    def __str__(self):
        return self.user.username

    @receiver(post_save, sender=settings.AUTH_USER_MODEL)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            UserProfile.objects.create(user=instance)

    @receiver(post_save, sender=settings.AUTH_USER_MODEL)
    def save_user_profile(sender, instance, **kwargs):
        instance.userprofile.save()


# Create your models here.
class Item(models.Model):
    title = models.CharField(max_length=200)
    price = models.FloatField()
    image = models.ImageField()
    discount_price = models.FloatField(blank=True, null=True)
    # category = models.CharField(choices=CATEGORY_CHOICES, max_length=2)
    category = models.ManyToManyField(Category)
    label = models.CharField(choices=LABEL_CHOICES, max_length=1, blank=True, null=True)
    label_name = models.CharField(choices=LABEL_NAME_CHOICES, max_length=1, blank=True, null=True)
    slug = models.SlugField()
    description = models.TextField()
    list_on_frontpage = models.BooleanField(default=False, blank=True, null=True)
    

    def __str__(self):
        return self.title


    def get_absolute_url(self):
        return reverse('product-page', kwargs={
            'slug': self.slug
        })

    def get_add_to_cart_url(self):
        return reverse('add-to-cart', kwargs={
            'slug': self.slug
        })
        
    def get_remove_from_cart_url(self):
        return reverse('remove-from-cart', kwargs={
            'slug': self.slug
        })
    
    def get_add_to_wishlist_url(self):
        return reverse('add-to-wishlist', kwargs={
            'slug': self.slug
        })

    def get_remove_from_wishlist_url(self):
        return reverse('remove-from-wishlist', kwargs={
            'slug': self.slug
        })

class OrderItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ordered = models.BooleanField(default=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} of {self.item.title}"

    def get_total_item_price(self):
        return self.quantity * self.item.price

    def get_total_item_discount_price(self):
        return self.quantity * self.item.discount_price

    def get_amount_saved(self):
        return self.get_total_item_price() - self.get_total_item_discount_price()

    def get_final_price(self):
        if self.item.discount_price:
            return self.get_total_item_discount_price()
        return self.get_total_item_price()


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    order_id = models.CharField(max_length=50)
    items = models.ManyToManyField(OrderItem)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField()
    ordered = models.BooleanField(default=False)
    billing_address = models.ForeignKey('BilingAddress', on_delete=models.SET_NULL, blank=True, null=True)
    payment = models.ForeignKey('Payment', on_delete=models.SET_NULL, blank=True, null=True)
    coupon = models.ForeignKey('DiscountCode', on_delete=models.SET_NULL, blank=True, null=True)
    in_transit = models.BooleanField(default=False)
    shipped = models.BooleanField(default=False)
    out_for_delivery = models.BooleanField(default=False)
    delivered = models.BooleanField(default=False)
    returned = models.BooleanField(default=False)
    refund_requested = models.BooleanField(default=False)
    refund_granted = models.BooleanField(default=False)
    canceled = models.BooleanField(default=False)


    def __str__(self):
        return self.user.username

    def get_total(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.get_final_price()
        if self.coupon:
            total -= self.coupon.amount
        return total


class BilingAddress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    address_type = models.CharField(choices=ADDRESS_TYPE_CHOICES, max_length=10, blank=True, null=True)
    street_address = models.CharField(max_length=255)
    apartment_address = models.CharField(max_length=255)
    country = CountryField(multiple=False) 
    zipcode = models.CharField(max_length=10)
    default_address = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username + ',' + self.street_address

    def get_absolute_url(self):
        return reverse('manage-address', kwargs={
            'id': self.id
        })


class Payment(models.Model):
    stripe_charge_id = models.CharField(max_length=50)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
    amount = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


#wishlisted products
class WishlistedItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, blank=True, null=True)
    wishlisted = models.BooleanField(default=False)


    def __str__(self):
        return f"{self.item.title}"


class Wishlish(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    item = models.ManyToManyField(WishlistedItem)
    wishlisted = models.BooleanField(default=False)
    wishlisted_date = models.DateTimeField(auto_now_add=False)

    def __str__(self):
        return self.user.username


#check in which area you service 
class CheckZipcode(models.Model):
    zipcode = models.CharField(max_length=10)

    def __str__(self):
        return self.zipcode


class DiscountCode(models.Model):
    promo_code = models.CharField(max_length=20)
    amount = models.FloatField()
    description = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.promo_code


class Refund(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    reason = models.TextField()
    refund_accepted = models.BooleanField(default=False)
    email = models.EmailField()

    def __str__(self):
        return f"{self.pk}"