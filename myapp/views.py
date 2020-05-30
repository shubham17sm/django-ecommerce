from django.conf import settings
from django.db.models import Q
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.views.generic import ListView, DetailView, View
from django.views.generic.edit import CreateView, UpdateView
from django.utils import timezone
from .models import Item, OrderItem, Order, BilingAddress, UserProfile, Payment, WishlistedItem, Wishlish, DiscountCode, CheckZipcode, Category, Refund
from .forms import CheckoutForm, CreateAddressForm, UserProfileForm, DiscountForm, CheckZipcodeForm, RequestRefundForm

import random
import string 

# Create your views here.
# def home_page(request):
#     items_queryset = Item.objects.all()
#     context = {
#         'items': items_queryset,
#     }
#     return render(request, "home-page.html", context)

# def get_user_profile(user): 
#     queryset = UserProfile.objects.filter(user=user)
#     if queryset.exists():
#         return queryset[0]
#     return None

import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


def create_order_id():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))


def search(request):
    queryset = Item.objects.all()
    query = request.GET.get('q')
    if query:
        queryset = queryset.filter(
            Q(title__icontains=query) |
            Q(category__title__icontains=query)
        ).distinct()
    context = {
        'queryset': queryset
    }
    return render(request, 'search.html', context)



class HomeView(ListView):
    model = Item
    context_object_name = 'object_list'
    queryset = Item.objects.filter(list_on_frontpage=True)
    paginate_by = 4
    template_name = "home-page.html"

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context['category'] = Category.objects.all()[:5]
        return context


class AllProductView(ListView):
    model = Item
    template_name = "all-product.html"


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'object': order
            }
            return render(self.request, 'order_summary.html', context)
        except ObjectDoesNotExist: 
            messages.error(self.request, "You do not have an active order")
            return redirect('/')

        
class WishlistView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            wishlist_qs = Wishlish.objects.get(user=self.request.user, wishlisted=False)
            context = {
                'wishlist': wishlist_qs
            }
            return render(self.request, 'wishlist.html', context)
        except ObjectDoesNotExist: 
            messages.error(self.request, "You have not added anything in wishlist yet")
            return redirect('/')


class PreviousOrderSummary(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            previous_order = Order.objects.filter(user=self.request.user, ordered=True)
            context = {
                'object': previous_order,
            }
            return render(self.request, 'previous_order.html', context)
        except ObjectDoesNotExist:
            messages.error(self.request, "You have not ordered anything yet")
            return redirect('/')


#my order page(currently)
class MyActiveOrderSummary(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            my_order = Order.objects.filter(user=self.request.user, ordered=True)
            context = {
                'object': my_order,
            }
            return render(self.request, 'my_active_order.html', context)
        except ObjectDoesNotExist:
            messages.error(self.request, "You have not ordered anything yet")
            return redirect('/')


class ItemDetailView(DetailView):
    model = Item
    template_name = "product-page.html"

    def get_context_data(self, **kwargs):
        context = super(ItemDetailView, self).get_context_data(**kwargs)
        context['zipcodeform'] = CheckZipcodeForm()
        return context


class CheckOutView(View):
    def get(self, *args, **kwargs):
        #form
        form = CheckoutForm()
        order = Order.objects.get(user=self.request.user, ordered=False)
        context = {
            'form': form,
            'object': order,
            'discountform': DiscountForm(),
            'DISPLAY_COUPON_FORM': True
        }
        return render(self.request, "checkout-page.html", context)
    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():
                street_address = form.cleaned_data.get('street_address')
                apartment_address = form.cleaned_data.get('apartment_address')
                country = form.cleaned_data.get('country')
                zipcode = form.cleaned_data.get('zipcode')
                # ToDo add functionalies for these two
                # same_shipping_address = forms.cleaned_data.get('same_shipping_address')
                # save_info = forms.cleaned_data.get('save_info')
                payment_option = form.cleaned_data.get('payment_option')
                billing_address = BilingAddress(
                    user = self.request.user,
                    street_address=street_address,
                    apartment_address=apartment_address,
                    country=country,
                    zipcode=zipcode
                )
                billing_address.save()
                order.billing_address = billing_address
                order.save()

                if payment_option == 'S':
                    return redirect('payment', payment_option='stripe')
                elif payment_option == 'P':
                    return redirect('payment', payment_option='paypal')
                else:
                    messages.warning(self.request, "Failed to checkout")
                    return redirect('checkout-page')
        except ObjectDoesNotExist: 
            messages.warning(self.request, "You do not have an active order")
            return redirect('all-product-view')


def cancel_order(request, id):
    order = Order.objects.get(user=request.user, ordered=True, id=id)
    try:
        order.in_transit = False
        order.shipped = False
        order.out_for_delivery = False
        order.delivered = False
        order.canceled = True
        order.save()

        messages.success(request, "Your order has been canceled")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    except ObjectDoesNotExist:
        messages.warning(request, "Order does not found")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


class PaymentView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        if order.billing_address:
            context = {
                'object': order,
                'DISPLAY_COUPON_FORM': False
            }
            return render(self.request, "payment.html", context) 
        else:
            messages.warning(self.request, "You have not entered billing address")
            return redirect('checkout-page')
    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        token = self.request.POST.get('stripeToken')
        #check again on amount line ..stripe doc for INR
        amount = int(order.get_total()* 100)


        try:
            charge = stripe.Charge.create(
                amount=amount,
                currency="inr",
                source=token,
            )
            #create the payment
            payment = Payment()
            payment.stripe_charge_id = charge['id']
            payment.user = self.request.user
            payment.amount = order.get_total()
            payment.save()

            #assign the payment to the order
            order_items = order.items.all()
            order_items.update(ordered=True)
            for item in order_items:
                item.save()

            order.ordered = True
            order.in_transit = True
            order.payment = payment
            order.order_id = create_order_id()
            order.save()

            messages.success(self.request, "Your order has been placed successfully")
            return redirect('/')

        except stripe.error.CardError as e:
           body = e.json_body
           err = body.get('error', {})
           messages.error(self.request, f"{err.get('message')}")
           return redirect('/')

        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            messages.error(self.request, "Rate limit error")
            return redirect('/')
            

        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            messages.error(self.request, "Invalid request error")
            return redirect('/')
            

        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            messages.error(self.request, "Not authenticated")
            return redirect('/')

        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            messages.error(self.request, "API connection error")
            return redirect('/')

        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
            messages.error(self.request, "Something went wrong")
            return redirect('/')

        except Exception as e:
            # send email to ourself
            messages.error(self.request, "Something went wrong! we are taking note of it")
            return redirect('/')



@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(item=item, user=request.user, ordered=False)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        #check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "This item was added to your cart.")
        else:
            messages.info(request, "This item was added to your cart.")
            order.items.add(order_item)
            return redirect('order-summary')
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "This item was added to your cart.")
        return redirect('order-summary')
    return redirect('order-summary')


@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user, 
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        #check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item, 
                user=request.user, 
                ordered=False
            )[0]
            order.items.remove(order_item)
            messages.info(request, "Removed from your cart.")
            return redirect('order-summary')
        else:
            messages.info(request, "This item was not in your cart.")
            return redirect('product-page', slug=slug) 
    else:
        #add a message saying the user doesnt have an order
        messages.info(request, "You do not have an active order.")
        return redirect('product-page', slug=slug)


#remove single item for the cart
@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user, 
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        #check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item, 
                user=request.user, 
                ordered=False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save() 
            else: 
                order.items.remove(order_item)
            messages.info(request, "This item quantity was updated")
            return redirect('order-summary')
        else:
            messages.info(request, "This item was not in your cart.")
            return redirect('product-page', slug=slug) 
    else:
        #add a message saying the user doesnt have an order
        messages.info(request, "You do not have an active order.")
        return redirect('product-page', slug=slug)



#wishlist-add to wishlist
@login_required
def add_to_wishlist(request, slug):
    item = get_object_or_404(Item, slug=slug)
    wishlist_item, created = WishlistedItem.objects.get_or_create(item=item, user=request.user, wishlisted=False)
    wishlist_qs = Wishlish.objects.filter(user=request.user, wishlisted=False)
    if wishlist_qs.exists():
        wishlist = wishlist_qs[0]
        #check if the order item is in the order
        if wishlist.item.filter(item__slug=item.slug).exists():
            wishlist_item.save()
            messages.info(request, "This item was added to your wishlist.")
        else:
            messages.info(request, "This item was added to your wishlist.")
            wishlist.item.add(wishlist_item)
            return redirect('product-page', slug=slug)
    else:
        wishlisted_date = timezone.now()
        wishlist = Wishlish.objects.create(user=request.user, wishlisted_date=wishlisted_date)
        wishlist.item.add(wishlist_item)
        messages.info(request, "This item was added to your wishlist.")
        return redirect('product-page', slug=slug)
    return redirect('product-page', slug=slug)


#remove from wishlist view
@login_required
def remove_from_wishlist(request, slug):
    item = get_object_or_404(Item, slug=slug)
    wishlist_qs = Wishlish.objects.filter(
        user=request.user, 
        wishlisted=False
    )
    if wishlist_qs.exists():
        wishlist = wishlist_qs[0]
        #check if the order item is in the order
        if wishlist.item.filter(item__slug=item.slug).exists():
            wishlist_item = WishlistedItem.objects.filter(
                item=item, 
                user=request.user, 
                wishlisted=False
            )[0]
            wishlist.item.remove(wishlist_item)
            messages.info(request, "Removed from your wishlist.")
            return redirect('wishlist-view')
        else:
            messages.info(request, "This item was not in your wishlist.")
            return redirect('product-page', slug=slug) 
    else:
        #add a message saying the user doesnt have an order
        messages.info(request, "You do not have an active product in your wishlist.")
        return redirect('product-page', slug=slug)



#add single item in the cart
# @login_required
# def add_single_item_from_cart(request, slug):
#     item = get_object_or_404(Item, slug=slug)
#     order_qs = Order.objects.filter(
#         user=request.user, 
#         ordered=False
#     )
#     if order_qs.exists():
#         order = order_qs[0]
#         #check if the order item is in the order
#         if order.items.filter(item__slug=item.slug).exists():
#             order_item = OrderItem.objects.filter(
#                 item=item, 
#                 user=request.user, 
#                 ordered=False
#             )[0]
#             order_item.quantity += 1
#             order_item.save()
#             messages.info(request, "This item quantity was updated")
#             return redirect('order-summary')
#         else:
#             messages.info(request, "This item was not in your cart.")
#             return redirect('product-page', slug=slug) 
#     else:
#         #add a message saying the user doesnt have an order
#         messages.info(request, "You do not have an active order.")
#         return redirect('product-page', slug=slug)
    

def profile_view(request):
    user = get_object_or_404(UserProfile, user=request.user)
    form = UserProfileForm(request.POST or None, request.FILES or None, instance=user)
    if form.is_valid():
        form.save()
        messages.info(request, "Your Profile has been updated")
        return redirect('profile')
    context = {
        'form': form,
        'user': user
    }
    return render(request, "user-profile.html", context)


def manage_address_view(request):
    qs = BilingAddress.objects.filter(user=request.user)
    user = get_object_or_404(UserProfile, user=request.user)
    context = {
        'qs': qs,
        'user': user
    }
    return render(request, "manage-address.html", context)


# class CreateAddress(CreateView):
#     def get(self, *args, **kwargs):
#         #form
#         form = CreateAddressForm()
#         title = 'Create'
#         context = {
#             'form': form,
#             'title': title
#         }
#         return render(self.request, "create-address.html", context)
#     def post(self, *args, **kwargs):
#         form = CreateAddressForm(self.request.POST or None)
#         if form.is_valid():
#             address_type = form.cleaned_data.get('address_type')
#             street_address = form.cleaned_data.get('street_address')
#             apartment_address = form.cleaned_data.get('apartment_address')
#             country = form.cleaned_data.get('country')
#             zipcode = form.cleaned_data.get('zipcode')
#             billing_address = BilingAddress(
#                     user = self.request.user,
#                     address_type=address_type,
#                     street_address=street_address,
#                     apartment_address=apartment_address,
#                     country=country,
#                     zipcode=zipcode
#             )
#             billing_address.save()
#             messages.info(self.request, "Your form has been submitted successfully")
#             return redirect('manage-address')
#         messages.warning(self.request, "Failed to update address")
#         return redirect('create-address')
    

# class UpdateAddress(UpdateView):
#     def get(self, *args, **kwargs):
#         #form
#         form = CreateAddressForm()
#         address = get_object_or_404(BilingAddress, id=self.id)
#         title = 'Update'
#         context = {
#             'form': form,
#             'title': title,
#             'address': address
#         }
#         return render(self.request, "create-address.html", context)
#     def post(self, *args, **kwargs):
#         form = CreateAddressForm(self.request.POST or None)
#         if form.is_valid():
#             address_type = form.cleaned_data.get('address_type')
#             street_address = form.cleaned_data.get('street_address')
#             apartment_address = form.cleaned_data.get('apartment_address')
#             country = form.cleaned_data.get('country')
#             zipcode = form.cleaned_data.get('zipcode')
#             billing_address = BilingAddress(
#                     user = self.request.user,
#                     address_type=address_type,
#                     street_address=street_address,
#                     apartment_address=apartment_address,
#                     country=country,
#                     zipcode=zipcode
#             )
#             billing_address.save()
#             messages.info(self.request, "Your form has been submitted successfully")
#             return redirect('manage-address', kwargs={
#                 'id': self.id
#             })
#         messages.warning(self.request, "Failed to update address")
#         return redirect('create-address')
    

#create manage address function
def address_create(request):
    title = 'Create'
    form = CreateAddressForm(request.POST or None)
    if form.is_valid():
        address_type = form.cleaned_data.get('address_type')
        street_address = form.cleaned_data.get('street_address')
        apartment_address = form.cleaned_data.get('apartment_address')
        country = form.cleaned_data.get('country')
        zipcode = form.cleaned_data.get('zipcode')
        default_address = form.cleaned_data.get('default_address')
        form = BilingAddress(
                user = request.user,
                address_type=address_type,
                street_address=street_address,
                apartment_address=apartment_address,
                country=country,
                zipcode=zipcode,
                default_address=default_address
        )
        form.save()
        messages.info(request, "Your form has been submitted successfully")
        return redirect('manage-address')
    context = {
        'form': form,
        'title': title
    }
    return render(request, "create-address.html", context)

#update manage address function
def address_update(request, id):
    title = 'Update'
    address = get_object_or_404(BilingAddress, id=id)
    form = CreateAddressForm(request.POST or None, request.FILES or None, instance=address)
    if form.is_valid():
        form.save()
        messages.info(request, "Your address has been updated successfully")
        return redirect('manage-address')
    context = {
        'form': form,
        'title': title
    }
    return render(request, "create-address.html", context)


def address_delete(request, id):
    address = get_object_or_404(BilingAddress, id=id)
    address.delete()
    messages.info(request, "Your address has been delete successfully")
    return redirect(reverse('manage-address'))


def get_coupon(request, promo_code):
    try:
        coupon = DiscountCode.objects.get(promo_code=promo_code)
        return coupon
    except ObjectDoesNotExist:
        messages.warning(request, "Promo code does not exists")
        return redirect('checkout-page')


class DiscountCodeView(View):
    def post(self, *args, **kwargs):
        form = DiscountForm(self.request.POST or None)
        if form.is_valid():
            try:
                promo_code = form.cleaned_data.get('promo_code')
                order = Order.objects.get(user = self.request.user, ordered = False)
                order.coupon = get_coupon(self.request, promo_code)
                order.save()
                messages.success(self.request, "Successfully applied coupon")
                return redirect('checkout-page')
            except ObjectDoesNotExist:
                messages.warning(self.request, "You do not have any active order")
                return redirect('checkout-page')
        else:
            messages.warning(self.request, "Promo code does not exists")
            return redirect('checkout-page')

#ToDo
def remove_coupon(request):
    order = Order.objects.get(user=request.user, ordered=False)
    order.coupon.delete()
    messages.warning(request, "Promo has been removed")
    return redirect('checkout-page')


def get_zipcode(request, zipcode):
    try:
        checkzip_qs = CheckZipcode.objects.get(zipcode=zipcode)
        messages.success(request, "This product is available at your location")
        return zipcode
    except ObjectDoesNotExist:
        messages.warning(request, "This product is not available at your location")
        return redirect('/')


class CheckZipcodeView(View):
    def post(self, *args, **kwargs):
        form = CheckZipcodeForm(self.request.POST or None)
        if form.is_valid():
            try:
                zipcode = form.cleaned_data.get('zipcode')
                checkzip_qs = get_zipcode(self.request, zipcode)
                return redirect('/')
            except ObjectDoesNotExist:
                return redirect('/')


#filter item by category
def item_by_category(request, slug):
    category = get_object_or_404(Category, slug=slug)
    item = Item.objects.filter(category=category)
    context = {
        'category':category,
        'items': item
    }
    return render(request, "item_by_cat.html", context)


class RequestRefundView(View):
    def get(self, *args, **kwargs):
        form = RequestRefundForm()
        context = {
            'form': form
        }
        return render(self.request, "refund_request.html", context)

    def post(self, *args, **kwargs):
        form = RequestRefundForm(self.request.POST)
        if form.is_valid():
            order_id = form.cleaned_data.get('order_id')
            message = form.cleaned_data.get('message')
            email = form.cleaned_data.get('email')
            try:
                order = Order.objects.get(order_id=order_id)
                order.refund_requested = True
                order.save()

                #store the refund
                refund = Refund()
                refund.order = order
                refund.reason = message
                refund.email = email
                refund.save()

                messages.info(self.request, "Your request has been submitted and our team will get in contact with you")
                return redirect('refund-view')

            except ObjectDoesNotExist:
                messages.warning(self.request, "This order does not exists")
                return redirect('refund-view')
