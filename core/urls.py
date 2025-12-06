from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.custom_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='core:login'), name='logout'),
    
    path('dashboard/', views.index, name='index'),
    path('monitor/', views.monitor, name='monitor'),
    path('checkin/', views.checkin_page, name='checkin'),
    path('checkout/', views.checkout_page, name='checkout'),
    path('history/', views.bill_history, name='bill_history'),
    path('history/<int:bill_id>/', views.bill_detail, name='bill_detail'),
    path('customer/<str:room_id>/', views.customer, name='customer'),
    
    
    # APIs
    path('api/rooms/', views.api_room_status, name='api_room_status'),
    path('api/room/<str:room_id>/', views.api_room_detail, name='api_room_detail'),
    path('api/control/<str:room_id>/', views.api_control_room, name='api_control_room'),
    path('api/checkin/', views.api_checkin, name='api_checkin'),
    path('api/checkout/', views.api_checkout, name='api_checkout'),
    path('api/queues/', views.api_scheduler_queues, name='api_scheduler_queues'),
]
