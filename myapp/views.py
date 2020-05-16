from django.conf import settings
from django.db.models import Q
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.views.generic import ListView, DetailView, View
from django.views.generic.edit import CreateView, UpdateView
from django.utils import timezone 
from .models import Item, OrderItem, Order, BilingAddress, UserProfile, Payment
from .forms import CheckoutForm, CreateAddressForm, UserProfileForm


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



def search(request):
    queryset = Item.objects.all()
    query = request.GET.get('q')
    if query:
        queryset = queryset.filter(
            Q(title__icontains=query)
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


class ItemDetailView(DetailView):
    model = Item
    template_name = "product-page.html"


class CheckOutView(View):
    def get(self, *args, **kwargs):
        #form
        form = CheckoutForm()
        order = Order.objects.get(user=self.request.user, ordered=False)
        context = {
            'form': form,
            'object': order
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
            messages.error(self.request, "You do not have an active order")
            return redirect('all-product-view')

class PaymentView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        context = {
            'object': order
        }
        return render(self.request, "payment.html", context)  
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
            order.ordered = True
            order.payment = payment
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
        form = BilingAddress(
                user = request.user,
                address_type=address_type,
                street_address=street_address,
                apartment_address=apartment_address,
                country=country,
                zipcode=zipcode
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

