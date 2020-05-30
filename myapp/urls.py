from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

from . import views


urlpatterns = [
    path('', views.HomeView.as_view(), name='home-page'),
    path('all-product/', views.AllProductView.as_view(), name='all-product-view'),
    path('product/<slug>/', views.ItemDetailView.as_view(), name='product-page'),
    path('order-summary/', views.OrderSummaryView.as_view(), name='order-summary'),
    path('add-to-cart/<slug>/', views.add_to_cart, name='add-to-cart'),
    path('remove-from-cart/<slug>/', views.remove_from_cart, name='remove-from-cart'),
    path('wishlist/', views.WishlistView.as_view(), name='wishlist-view'),
    path('add-to-wishlist/<slug>/', views.add_to_wishlist, name='add-to-wishlist'),
    path('remove-from-wishlist/<slug>/', views.remove_from_wishlist, name='remove-from-wishlist'),
    path('remove-single-item-from-cart/<slug>/', views.remove_single_item_from_cart, name='remove-single-item-from-cart'),
    # path('add-single-item-from-cart/<slug>/', views.add_single_item_from_cart, name='add-single-item-from-cart'),
    path('checkout/', views.CheckOutView.as_view(), name='checkout-page'),
    path('payment/<payment_option>/', views.PaymentView.as_view(), name='payment'),
    path('manage-address/', views.manage_address_view, name='manage-address'),
    path('create-address/', views.address_create, name='create-address'),
    path('update-address/<id>/', views.address_update, name='update-address'),
    path('delete-address/<id>/', views.address_delete, name='delete-address'),
    path('accounts/profile/', views.profile_view, name='profile'),
    path('pervious-order/', views.PreviousOrderSummary.as_view(), name='previous-order'),
    path('discount-code/', views.DiscountCodeView.as_view(), name='discount-code'),
    path('remove-code/', views.remove_coupon, name='remove-code'),
    path('check-zipcode/', views.CheckZipcodeView.as_view(), name='check-zipcode'),
    path('cat/<slug>/', views.item_by_category, name='item-by-category'),
    path('refund-request/', views.RequestRefundView.as_view(), name='refund-view'),
    path('my-active-order/', views.MyActiveOrderSummary.as_view(), name='my-active-order'),
    path('cancel-order/<id>/', views.cancel_order, name='cancel-order'),
    path('search/', views.search, name='search'),
    path('accounts/', include('allauth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
