from django.contrib import admin
from django.urls import path, include
from loans import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'), 
    path('kyc/', views.update_kyc, name='update_kyc'),
    path('apply/', views.apply_loan, name='apply_loan'),
    path('profile/', views.profile_view, name='profile'),
    path('my-loans/', views.my_loans_view, name='my_loans'),
    path('payments/', views.payments_view, name='payments'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('payments/', views.payments_view, name='payments'),
    path('pay/<int:emi_id>/', views.initiate_payment, name='initiate_payment'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('history/', views.transaction_history_view, name='history'),
    path('support/', views.support_view, name='support'),
]