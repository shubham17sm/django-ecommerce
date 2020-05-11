from django.db.models import Q
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, View
from django.utils import timezone 
from .models import Item, OrderItem, Order, BilingAddress
from .forms import CheckoutForm

# Create your views here.
# def home_page(request):
#     items_queryset = Item.objects.all()
#     context = {
#         'items': items_queryset,
#     }
#     return render(request, "home-page.html", context)

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
                # ToDo : add redirect to the selected payment option
                #remove below message anytime
                messages.info(self.request, "Your form has been submitted successfully")
                return redirect('checkout-page')
            messages.warning(self.request, "Failed to checkout")
            return redirect('checkout-page')
        except ObjectDoesNotExist: 
            messages.error(self.request, "You do not have an active order")
            return redirect('all-product-view')

        



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
    return render(request, "user-profile.html", {})


def manage_address_view(request):
    qs = BilingAddress.objects.filter(user=request.user)
    context = {
        'qs': qs
    }
    return render(request, "manage-address.html", context)

# def create_address(request):
#     title = 'Create'
#     qs = BilingAddress(request.POST or None)
#     user = 