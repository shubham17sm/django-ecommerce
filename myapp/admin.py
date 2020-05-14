from django.contrib import admin
from .models import Item, OrderItem, Order, BilingAddress, UserProfile
# Register your models here.
admin.site.register(OrderItem)
admin.site.register(Order)
admin.site.register(UserProfile)


class BilingAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'country', 'zipcode', 'address_type')

admin.site.register(BilingAddress, BilingAddressAdmin)


class ItemDisplayAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'list_on_frontpage')
    list_filter = ('category',)
    search_fields = ('title', 'category', 'description', 'slug')

admin.site.register(Item, ItemDisplayAdmin)