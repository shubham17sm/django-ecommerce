from django.contrib import admin
from .models import Item, OrderItem, Order, BilingAddress, UserProfile, Payment, CheckZipcode, WishlistedItem, Wishlish, DiscountCode, Category, Refund
# Register your models here.
admin.site.register(OrderItem)
admin.site.register(UserProfile)
admin.site.register(WishlistedItem)
admin.site.register(Wishlish)
admin.site.register(Category)
admin.site.register(Refund)


class ItemDisplayAdmin(admin.ModelAdmin):
    list_display = ('title', 'list_on_frontpage')
    list_filter = ('category',)
    search_fields = ('title', 'category', 'description', 'slug')

admin.site.register(Item, ItemDisplayAdmin)


class PaymentAdminDisplay(admin.ModelAdmin):
    list_display = ('user', 'stripe_charge_id', 'amount')
    search_fields = ('user__username', 'stripe_charge_id')

admin.site.register(Payment, PaymentAdminDisplay)


def make_refund_accepted(modeladmin, request, queryset):
    queryset.update(refund_requested=False, refund_granted=True)

make_refund_accepted.short_description = 'Update orders to refund granted'

def make_order_is_shipped(modeladmin, request, queryset):
    queryset.update(in_transit=False, shipped=True)

make_order_is_shipped.short_description = 'Update order from in transit to shipped'


def make_order_is_out_for_delivery(modeladmin, request, queryset):
    queryset.update(shipped=False, out_for_delivery=True)

make_order_is_out_for_delivery.short_description = 'Update order shipped to out for delivery'


def make_order_is_delivered(modeladmin, request, queryset):
    queryset.update(out_for_delivery=False, delivered=True)

make_order_is_delivered.short_description = 'Update order out for delivery to delivered'

def make_order_is_returned(modeladmin, request, queryset):
    queryset.update(delivered=False, returned=True)

make_order_is_returned.short_description = 'Update order from delivered to return'


class BilingAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'country', 'zipcode', 'address_type')

admin.site.register(BilingAddress, BilingAddressAdmin)


class OrderAdminDisplay(admin.ModelAdmin):
    list_display = ('user',
                    'order_id',
                    'ordered', 
                    'billing_address', 
                    'payment',
                    'coupon',
                    'in_transit',
                    'shipped',
                    'out_for_delivery',
                    'delivered',
                    'returned',
                    'canceled',
                    'refund_requested',
                    'refund_granted',)
    list_display_links = ('user',
                            'billing_address',
                            'payment',
                            'coupon')
    list_filter = ('ordered', 
                    'in_transit',
                    'shipped',
                    'out_for_delivery',
                    'delivered',
                    'returned',
                    'canceled',
                    'refund_requested',
                    'refund_granted')
    search_fields = ('user__username', 'order_id')
    actions = [make_refund_accepted, make_order_is_shipped, make_order_is_out_for_delivery, make_order_is_delivered, make_order_is_returned]

admin.site.register(Order, OrderAdminDisplay)


class CheckZipcodeForDelivery(admin.ModelAdmin):
    search_fields = ('zipcode',)

admin.site.register(CheckZipcode, CheckZipcodeForDelivery)


class DiscountCodeAdmin(admin.ModelAdmin):
    list_display = ('promo_code', 'amount', 'description')
    search_fields = ('promo_code',)

admin.site.register(DiscountCode, DiscountCodeAdmin)