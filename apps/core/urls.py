from django.urls import path
from .views import LoginView, EventListView, PromoValidateView, OrderListCreateView

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="api-login"),
    path("events/", EventListView.as_view(), name="api-events"),
    path("promos/validate/", PromoValidateView.as_view(), name="api-promo-validate"),
    path("orders/", OrderListCreateView.as_view(), name="api-orders"),
]
