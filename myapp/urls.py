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
    path('remove-single-item-from-cart/<slug>/', views.remove_single_item_from_cart, name='remove-single-item-from-cart'),
    # path('add-single-item-from-cart/<slug>/', views.add_single_item_from_cart, name='add-single-item-from-cart'),
    path('checkout/', views.checkout_page, name='checkout-page'),
    path('search/', views.search, name='search'),
    path('accounts/', include('allauth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
